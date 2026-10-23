"""Canonical evidence adapter for the case-based Contact 1 runtime."""

from openai import OpenAIError

from .agent_harness import InvestigationFailure
from .contact2.config import RagFailure


def retrieve_evidence(store, actor, question, retrieve, rag):
    documents = store.documents(actor)
    allowed = {d["id"]: d for d in documents}
    if rag is not None:
        with rag.lock:
            calls, tokens = rag.embedding_calls, rag.embedding_tokens
            try:
                hits, trace = rag.search(documents, question, actor)
            except (RagFailure, OpenAIError) as error:
                failure = (
                    error.args[0] if isinstance(error, RagFailure) else "embedding_provider_error"
                )
                return (
                    [],
                    {
                        "retrieval": rag.config.mode,
                        "embedding_model": rag.config.model,
                        "embedding_calls": rag.embedding_calls - calls,
                        "embedding_input_tokens": rag.embedding_tokens - tokens
                        if rag.usage_complete
                        else None,
                    },
                    failure,
                )
        evidence = []
        for hit in hits:
            d = allowed.get(hit["id"])
            if d is None or hit["excerpt"] != d["text"][hit["start"] : hit["end"]]:
                raise InvestigationFailure("invalid_canonical_chunk")
            evidence.append(
                {
                    k: hit[k]
                    for k in (
                        "id",
                        "title",
                        "version",
                        "excerpt",
                        "chunk_id",
                        "start",
                        "end",
                        "score",
                        "vector_score",
                    )
                }
            )
        return evidence, trace, None
    evidence = [
        {"id": d["id"], "title": d["title"], "version": d["version"], "excerpt": d["text"]}
        for d in {
            d["id"]: allowed[d["id"]]
            for d in retrieve(documents, question)
            if d.get("id") in allowed
        }.values()
    ]
    return evidence, {"retrieval": retrieve.__name__, "embedding_calls": 0}, None
