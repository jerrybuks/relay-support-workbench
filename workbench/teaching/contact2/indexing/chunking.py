"""Split canonical text into passages, retaining source identity and exact offsets.

The LangChain option uses RecursiveCharacterTextSplitter. The native option remains
available for existing indexes; changing a splitter requires a separately rebuilt index.
"""

import uuid

from ..config import RagFailure, source_hash


def pages_for_span(document, start, end):
    """Original PDF pages whose extracted text overlaps this half-open span."""
    return [
        page["page"]
        for page in document.get("page_ranges", [])
        if page["start"] < end and start < page["end"]
    ]


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
                "pages": pages_for_span(document, start, end),
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
                "pages": pages_for_span(document, start, end),
                "source_hash": fingerprint,
                "tenant": document["tenant"],
                "visibility": document["visibility"],
                "state": document["state"],
            }
        )
    return result
