"""Compatibility imports for Contact 1 scripts and existing teaching callers.

The shared, working stages now live in contact2/indexing and contact2/querying.
The baseline never imports this optional pipeline.
"""

from .contact2.config import RagConfig, RagFailure, digest, source_hash
from .contact2.indexing.chunking import chunks, native_chunks
from .contact2.indexing.vector_store import VectorStore as VectorRag
from .contact2.querying.retrieval import search_query

__all__ = [
    "RagConfig",
    "RagFailure",
    "digest",
    "source_hash",
    "chunks",
    "native_chunks",
    "VectorRag",
    "search_query",
]
