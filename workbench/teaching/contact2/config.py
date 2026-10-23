"""Shared RAG settings and source identities. Configuration does not make API calls."""

import hashlib
import json
import os
from dataclasses import asdict, dataclass

from ..provider_connection import model_setting


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


def source_hash(document):
    identity = {
        k: document.get(k)
        for k in ("id", "tenant", "title", "version", "text", "tags", "state", "visibility")
    }
    # Retain legacy identities for sources without PDF provenance.
    if "page_ranges" in document:
        identity["page_ranges"] = document["page_ranges"]
    return digest(identity)
