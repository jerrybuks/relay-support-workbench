"""Embed a question, search permitted passages and verify canonical evidence."""

import re
import time

from qdrant_client import models

from ...contact1_reference import search_reference
from ...observability_reference import stage
from ..config import RagFailure, source_hash
from ..indexing.chunking import chunks


def retrieve_passages(index, documents, question, actor):
    with index.lock:
        started = time.perf_counter()
        manifest = index.manifest()
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
        canonical = {c["chunk_id"]: c for d in allowed for c in chunks(d, index.config)}
        if not canonical:
            return [], {"embedding_calls": 0, "retrieval": index.config.mode}
        calls, tokens = index.embedding_calls, index.embedding_tokens
        query = search_query(question, allowed)
        vector = index.embeddings.embed([query])[0]
        scope = models.Filter(
            must=[
                models.HasIdCondition(has_id=list(canonical)),
                models.FieldCondition(key="tenant", match=models.MatchValue(value=actor.tenant)),
                models.FieldCondition(key="state", match=models.MatchValue(value="published")),
            ]
        )
        with stage("vector_search", "retriever"):
            points = index.db.query_points(
                manifest["collection"],
                query=vector,
                query_filter=scope,
                limit=10,
                score_threshold=index.config.min_score,
                with_payload=False,
            ).points
        ranked = [(str(p.id), p.score) for p in points]
        cosine = dict(ranked)
        if index.config.mode == "hybrid":
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
            for key, score in ranked[: index.config.top_k]
        ]
        return hits, {
            "retrieval": index.config.mode,
            "query_normalized": query != question,
            "vector_hits": len(points),
            "embedding_model": index.config.model,
            "embedding_dimensions": index.config.dimensions,
            "embedding_calls": index.embedding_calls - calls,
            "embedding_input_tokens": index.embedding_tokens - tokens
            if index.usage_complete
            else None,
            "corpus_version": manifest["revision"],
            "chunk_count": manifest["chunks"],
            "retrieval_ms": round((time.perf_counter() - started) * 1000, 2),
            "min_vector_score": index.config.min_score,
            "retrieved_chunks": [
                {k: c[k] for k in ("id", "chunk_id", "start", "end", "score", "vector_score")}
                for c in hits
            ],
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
