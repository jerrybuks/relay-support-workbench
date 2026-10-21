"""Prepared C1 RAG: OpenAI embeddings and persistent, permission-filtered Qdrant.

Local Qdrant is a single-process development store. Indexing is an explicit command,
never a startup side effect. The baseline does not import this module.
"""

import hashlib
import json
import math
import os
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from qdrant_client import QdrantClient, models

from .contact1_reference import search_reference
from .observability_reference import stage
from .provider_connection import model_setting, provider_name, vector_path

ROOT = Path(__file__).resolve().parents[1]


class RagFailure(ValueError):
    """Fixed safe codes only; provider errors are handled at the API boundary."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class RagConfig:
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    chunk_size: int = 320
    overlap: int = 64
    top_k: int = 3
    min_score: float = 0.4
    mode: str = "vector"
    chunker: str = "native"

    def __post_init__(self):
        if (
            not self.model
            or not 1 <= self.dimensions <= 3072
            or not 128 <= self.chunk_size <= 2000
            or not 0 <= self.overlap < self.chunk_size // 2
            or not 1 <= self.top_k <= 10
            or not -1 <= self.min_score <= 1
            or self.mode not in {"vector", "hybrid"}
            or self.chunker not in {"native", "langchain"}
        ):
            raise RagFailure("invalid_rag_configuration")

    @classmethod
    def environment(cls):
        return cls(
            model=model_setting(embedding=True),
            dimensions=int(os.getenv("RELAY_EMBEDDING_DIMENSIONS", "1536")),
            chunker=os.getenv("RELAY_CHUNKER", "native"),
            mode=os.getenv("RELAY_RETRIEVAL_MODE", "hybrid"),
            min_score=float(os.getenv("RELAY_VECTOR_MIN_SCORE", "0.4")),
        )

    def index_settings(self):
        return {
            k: asdict(self)[k] for k in ("model", "dimensions", "chunk_size", "overlap", "chunker")
        }


def search_query(question, documents):
    """Repair one missing letter only when the permitted policy vocabulary is unambiguous.

    Never use restricted sources to suggest words, expand instructions or replace the
    original question sent to the answer model. This is retrieval preprocessing only.
    """

    def words(text):
        return set(re.findall(r"[a-z]+", text.lower()))

    candidates = set()
    known = words(question) & {"please", "could", "would", "should", "their", "there"}
    for document in documents:
        candidates |= words(document["title"] + " " + document.get("tags", ""))
        known |= words(document["text"])
    known |= candidates

    def correct(match):
        word = match.group().lower()
        if word in known:
            return match.group()
        matches = [
            candidate
            for candidate in candidates
            if len(candidate) == len(word) + 1
            and any(candidate[:i] + candidate[i + 1 :] == word for i in range(len(candidate)))
        ]
        return matches[0] if len(matches) == 1 else match.group()

    return re.sub(r"\b[a-zA-Z]{5,}\b", correct, question)


def source_hash(document):
    return digest(
        {
            k: document.get(k)
            for k in ("id", "tenant", "title", "version", "text", "tags", "state", "visibility")
        }
    )


def native_chunks(document, config):
    text = document["text"]
    if not text.strip() or len(text) > 100_000:
        raise RagFailure("invalid_source_size")
    start = 0
    result = []
    fingerprint = source_hash(document)
    while start < len(text):
        end = min(start + config.chunk_size, len(text))
        # Keep words intact while retaining exact offsets into canonical source text.
        if end < len(text):
            split = text.rfind(" ", start + config.chunk_size // 2, end)
            if split > start:
                end = split
        key = f"{fingerprint}:{config.chunk_size}:{config.overlap}:{start}:{end}"
        result.append(
            {
                "chunk_id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                "id": document["id"],
                "title": document["title"],
                "version": document["version"],
                "excerpt": text[start:end],
                "start": start,
                "end": end,
                "source_hash": fingerprint,
                "tenant": document["tenant"],
                "visibility": document["visibility"],
                "state": document["state"],
            }
        )
        if end == len(text):
            break
        start = max(start + 1, end - config.overlap)
        while start < end and not text[start - 1].isspace():
            start += 1
    return result


def chunks(document, config):
    if config.chunker == "native":
        return native_chunks(document, config)
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    if not document["text"].strip() or len(document["text"]) > 100_000:
        raise RagFailure("invalid_source_size")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.overlap,
        add_start_index=True,
        strip_whitespace=False,
    )
    fingerprint = source_hash(document)
    result = []
    for item in splitter.create_documents([document["text"]]):
        start = item.metadata["start_index"]
        end = start + len(item.page_content)
        if start < 0 or item.page_content != document["text"][start:end]:
            raise RagFailure("invalid_chunk_offsets")
        key = f"langchain:{fingerprint}:{config.chunk_size}:{config.overlap}:{start}:{end}"
        result.append(
            {
                "chunk_id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                "id": document["id"],
                "title": document["title"],
                "version": document["version"],
                "excerpt": item.page_content,
                "start": start,
                "end": end,
                "source_hash": fingerprint,
                "tenant": document["tenant"],
                "visibility": document["visibility"],
                "state": document["state"],
            }
        )
    return result


class VectorRag:
    def __init__(self, client, path=None, config=None):
        self.client = client
        self.config = config or RagConfig.environment()
        self.path = Path(path) if path else vector_path()
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = QdrantClient(path=str(self.path), force_disable_check_same_thread=True)
        self.lock = threading.RLock()
        self.manifest_path = self.path / "relay-manifest.json"
        self.embedding_calls = 0
        self.embedding_tokens = 0
        self.usage_complete = True

    def close(self):
        self.db.close()

    def _embed(self, inputs):
        tokens = self.embedding_tokens
        with stage("query_or_document_embedding", "embedding", self.config.model) as measurement:
            result = self._embed_request(inputs)
            if self.usage_complete:
                measurement.update(input_tokens=self.embedding_tokens - tokens, output_tokens=0)
            return result

    def _embed_request(self, inputs):
        self.embedding_calls += 1  # Attempts, including failures; SDK retries are disabled.
        try:
            response = self.client.embeddings.create(
                model=self.config.model,
                dimensions=self.config.dimensions,
                input=inputs,
                encoding_format="float",
            )
        except Exception:
            self.usage_complete = False
            raise
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.embedding_tokens += usage.prompt_tokens
        else:
            self.usage_complete = False
        rows = sorted(response.data, key=lambda r: r.index)
        if [r.index for r in rows] != list(range(len(inputs))):
            raise RagFailure("invalid_embedding_indices")
        vectors = [r.embedding for r in rows]
        if any(
            len(v) != self.config.dimensions
            or any(not math.isfinite(x) for x in v)
            or not any(x != 0 for x in v)
            for v in vectors
        ):
            raise RagFailure("invalid_embedding_vector")
        accepted_models = {self.config.model}
        if provider_name(self.client) == "openrouter" and self.config.model.startswith("openai/"):
            # Live OpenRouter returns the upstream bare ID for its namespaced route.
            # Accept only the exact same model; never match an arbitrary suffix/provider.
            accepted_models.add(self.config.model.removeprefix("openai/"))
        if response.model not in accepted_models:
            raise RagFailure("embedding_model_mismatch")
        return vectors

    def manifest(self):
        try:
            manifest = json.loads(self.manifest_path.read_text())
        except (OSError, ValueError):
            raise RagFailure("vector_index_missing_or_invalid") from None
        if (
            not isinstance(manifest, dict)
            or not isinstance(manifest.get("collection"), str)
            or not isinstance(manifest.get("sources"), dict)
            or not isinstance(manifest.get("revision"), str)
            or not isinstance(manifest.get("chunks"), int)
        ):
            raise RagFailure("vector_index_missing_or_invalid")
        if manifest.get("settings") != self.config.index_settings():
            raise RagFailure("vector_index_configuration_mismatch")
        if not self.db.collection_exists(manifest["collection"]):
            raise RagFailure("vector_collection_missing")
        return manifest

    def build(self, documents):
        """Atomic manifest switch; unchanged chunk vectors are reused without API calls."""
        with self.lock:
            if not documents or any(d["state"] != "published" for d in documents):
                raise RagFailure("index_requires_published_sources")
            if len({d["id"] for d in documents}) != len(documents):
                raise RagFailure("duplicate_source_ids")
            all_chunks = [c for d in documents for c in chunks(d, self.config)]
            if len(all_chunks) > 1000:
                raise RagFailure("local_index_budget_exceeded")
            old = None
            if self.manifest_path.exists():
                old = self.manifest()  # Configuration changes require a separate index path.
            collection = "relay_" + uuid.uuid4().hex
            self.db.create_collection(
                collection,
                vectors_config=models.VectorParams(
                    size=self.config.dimensions, distance=models.Distance.COSINE
                ),
            )
            calls, tokens = self.embedding_calls, self.embedding_tokens
            reused = 0
            try:
                for offset in range(0, len(all_chunks), 32):
                    batch = all_chunks[offset : offset + 32]
                    cached = {}
                    if old:
                        cached = {
                            str(p.id): p.vector
                            for p in self.db.retrieve(
                                old["collection"],
                                ids=[c["chunk_id"] for c in batch],
                                with_vectors=True,
                                with_payload=False,
                            )
                        }
                    missing = [c for c in batch if c["chunk_id"] not in cached]
                    if missing:
                        vectors = self._embed([c["excerpt"] for c in missing])
                        cached.update(zip([c["chunk_id"] for c in missing], vectors, strict=True))
                    reused += len(batch) - len(missing)
                    self.db.upsert(
                        collection,
                        points=[
                            models.PointStruct(
                                id=c["chunk_id"], vector=cached[c["chunk_id"]], payload=c
                            )
                            for c in batch
                        ],
                        wait=True,
                    )
                manifest = {
                    "collection": collection,
                    "settings": self.config.index_settings(),
                    "sources": {d["id"]: source_hash(d) for d in documents},
                    "revision": digest(sorted(c["chunk_id"] for c in all_chunks)),
                    "chunks": len(all_chunks),
                }
                temporary = self.manifest_path.with_suffix(".tmp")
                temporary.write_text(json.dumps(manifest, indent=2) + "\n")
                temporary.replace(self.manifest_path)
            except Exception:
                self.db.delete_collection(collection)
                raise
            if old:
                self.db.delete_collection(old["collection"])
            return {
                **manifest,
                "embedding_calls": self.embedding_calls - calls,
                "embedding_input_tokens": self.embedding_tokens - tokens
                if self.usage_complete
                else None,
                "reused_chunks": reused,
            }

    def search(self, documents, question, actor):
        with self.lock:
            started = time.perf_counter()
            manifest = self.manifest()
            allowed = [
                d
                for d in documents
                if d["tenant"] == actor.tenant
                and d["state"] == "published"
                and (d["visibility"] == "team" or actor.role == "supervisor")
            ]
            # New/changed permitted sources must be reindexed; never serve stale text.
            if any(manifest["sources"].get(d["id"]) != source_hash(d) for d in allowed):
                raise RagFailure("vector_index_stale_or_scope_incomplete")
            canonical = {c["chunk_id"]: c for d in allowed for c in chunks(d, self.config)}
            if not canonical:
                return [], {"embedding_calls": 0, "retrieval": self.config.mode}
            calls, tokens = self.embedding_calls, self.embedding_tokens
            query = search_query(question, allowed)
            vector = self._embed([query])[0]
            scope = models.Filter(
                must=[
                    models.HasIdCondition(has_id=list(canonical)),
                    models.FieldCondition(
                        key="tenant", match=models.MatchValue(value=actor.tenant)
                    ),
                    models.FieldCondition(key="state", match=models.MatchValue(value="published")),
                ]
            )
            with stage("vector_search", "retriever"):
                points = self.db.query_points(
                    manifest["collection"],
                    query=vector,
                    query_filter=scope,
                    limit=10,
                    score_threshold=self.config.min_score,
                    with_payload=False,
                ).points
            ranked = [(str(p.id), p.score) for p in points]
            cosine = dict(ranked)
            if self.config.mode == "hybrid":
                # RRF combines vector ranks with permissioned FTS ranks; scores differ in scale.
                lexical = search_reference(allowed, query)
                lexical_ids = [
                    c["chunk_id"] for d in lexical for c in canonical.values() if c["id"] == d["id"]
                ]
                scores = {}
                for ordering in ([key for key, _ in ranked], lexical_ids):
                    for rank, key in enumerate(ordering, 1):
                        scores[key] = scores.get(key, 0) + 1 / (60 + rank)
                ranked = sorted(scores.items(), key=lambda p: (-p[1], p[0]))
            hits = [
                {**canonical[key], "score": float(score), "vector_score": cosine.get(key)}
                for key, score in ranked[: self.config.top_k]
            ]
            return hits, {
                "retrieval": self.config.mode,
                "query_normalized": query != question,
                "vector_hits": len(points),
                "embedding_model": self.config.model,
                "embedding_dimensions": self.config.dimensions,
                "embedding_calls": self.embedding_calls - calls,
                "embedding_input_tokens": self.embedding_tokens - tokens
                if self.usage_complete
                else None,
                "corpus_version": manifest["revision"],
                "chunk_count": manifest["chunks"],
                "retrieval_ms": round((time.perf_counter() - started) * 1000, 2),
                "min_vector_score": self.config.min_score,
                "retrieved_chunks": [
                    {k: c[k] for k in ("id", "chunk_id", "start", "end", "score", "vector_score")}
                    for c in hits
                ],
            }
