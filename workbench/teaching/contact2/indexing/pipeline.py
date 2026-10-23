"""Start here: PDF preview, then chunk → embed → store after human review.

preview_pdf is offline and feeds the review screen. build_index is the single
indexing coordinator; it accepts the reviewed canonical source documents.
"""

from ..config import RagFailure
from .chunking import chunks
from .parsing import extract_pdf


def preview_pdf(raw, metadata, config):
    """Parse the PDF and show its chunks before authorizing embedding requests."""
    text, pages = extract_pdf(raw)
    source = {**metadata, "text": text}
    passages = chunks(source, config)
    return source, pages, passages


def build_index(index, documents, *, allow_embeddings=True):
    """Chunk reviewed documents, embed new passages, then save the complete index."""
    with index.lock:
        if not documents or any(d["state"] != "published" for d in documents):
            raise RagFailure("index_requires_published_sources")
        if len({d["id"] for d in documents}) != len(documents):
            raise RagFailure("duplicate_source_ids")

        # 1. Chunk the reviewed, canonical text.
        passages = [passage for document in documents for passage in chunks(document, index.config)]
        if len(passages) > 1000:
            raise RagFailure("local_index_budget_exceeded")

        # 2. Embed new passages; reuse vectors already stored for unchanged chunks.
        cached = index.cached_vectors(passages)
        calls, tokens = index.embedding_calls, index.embedding_tokens
        vectors = index.embeddings.embed_passages(
            passages, cached, allow_embeddings=allow_embeddings
        )

        # 3. Store vectors and passages, then publish the new index atomically.
        manifest = index.save(documents, passages, vectors)
        return {
            **manifest,
            "embedding_calls": index.embedding_calls - calls,
            "embedding_input_tokens": index.embedding_tokens - tokens
            if index.usage_complete
            else None,
            "reused_chunks": len(cached),
        }
