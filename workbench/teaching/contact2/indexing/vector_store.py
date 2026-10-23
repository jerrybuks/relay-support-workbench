"""Persist Qdrant vectors and atomically publish an index after successful embedding."""

import json
import threading
import uuid
from pathlib import Path

from qdrant_client import QdrantClient, models

from ...provider_connection import vector_path
from ..config import RagConfig, RagFailure, digest, source_hash
from ..querying.retrieval import retrieve_passages
from .embeddings import EmbeddingModel
from .pipeline import build_index


class VectorStore:
    def __init__(self, client, path=None, config=None):
        self.client = client
        self.config = config or RagConfig.environment()
        self.path = Path(path) if path else vector_path()
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = QdrantClient(path=str(self.path), force_disable_check_same_thread=True)
        self.lock = threading.RLock()
        self.manifest_path = self.path / "relay-manifest.json"
        self.embeddings = EmbeddingModel(client, self.config)

    def close(self):
        self.db.close()

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

    def cached_vectors(self, passages):
        """Read reusable vectors from the current index without a provider request."""
        if not self.manifest_path.exists():
            return {}
        current = self.manifest()
        return {
            str(point.id): point.vector
            for point in self.db.retrieve(
                current["collection"],
                ids=[p["chunk_id"] for p in passages],
                with_vectors=True,
                with_payload=False,
            )
        }

    def save(self, documents, passages, vectors):
        """Write prepared vectors and passages; retain the old index if writing fails."""
        previous = self.manifest() if self.manifest_path.exists() else None
        collection = "relay_" + uuid.uuid4().hex
        self.db.create_collection(
            collection,
            vectors_config=models.VectorParams(
                size=self.config.dimensions,
                distance=models.Distance.COSINE,
            ),
        )
        try:
            for offset in range(0, len(passages), 32):
                self.db.upsert(
                    collection,
                    points=[
                        models.PointStruct(
                            id=p["chunk_id"],
                            vector=vectors[p["chunk_id"]],
                            payload=p,
                        )
                        for p in passages[offset : offset + 32]
                    ],
                    wait=True,
                )
            manifest = {
                "collection": collection,
                "settings": self.config.index_settings(),
                "sources": {d["id"]: source_hash(d) for d in documents},
                "revision": digest(sorted(p["chunk_id"] for p in passages)),
                "chunks": len(passages),
            }
            temporary = self.manifest_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(manifest, indent=2) + "\n")
            temporary.replace(self.manifest_path)
        except Exception:
            self.db.delete_collection(collection)
            raise
        if previous:
            self.db.delete_collection(previous["collection"])
        return manifest

    def build(self, documents, *, allow_embeddings=True):
        """Existing scripts use build(); orchestration is in indexing/pipeline.py."""
        return build_index(self, documents, allow_embeddings=allow_embeddings)

    @property
    def embedding_calls(self):
        return self.embeddings.embedding_calls

    @property
    def embedding_tokens(self):
        return self.embeddings.embedding_tokens

    @property
    def usage_complete(self):
        return self.embeddings.usage_complete

    def search(self, documents, question, actor):
        return retrieve_passages(self, documents, question, actor)
