"""Opt-in Contact 1 app composition; baseline imports no teaching code."""

from openai import OpenAIError
from pydantic import Field

from relay.main import create_app as baseline
from relay.models import Contract
from relay.store import Store

from .agent_harness import LiveAsk
from .contact1_reference import search_reference
from .investigation_reference import PROMPT_VERSION, make_investigator  # noqa: F401
from .provider_connection import provider_name
from .rag_reference import RagFailure, VectorRag
from .responses_reference import live_client


class RagQuery(Contract):
    question: str = Field(min_length=3, max_length=1500)


def create_app(
    db_path=None,
    *,
    client=None,
    model=None,
    trace_client=None,
    retriever=None,
    vector_path=None,
    rag_config=None,
    store_factory=Store,
    checkpoint="contact-1-live-reference",
    session_cookie="relay_c1_live",
):
    import os
    from pathlib import Path

    # Injected clients exist for local contract tests; normal startup must opt in explicitly.
    if client is None:
        client, model = live_client()
    if not model:
        raise RuntimeError("Configure a model before starting the live reference.")
    path = db_path or os.getenv(
        "RELAY_REFERENCE_DB", str(Path(__file__).parents[1] / ".runtime/c1-live.sqlite")
    )
    rag = None if retriever else VectorRag(client, vector_path, rag_config)
    app = baseline(
        path,
        retriever=retriever or search_reference,
        checkpoint=checkpoint,
        store_factory=store_factory,
        investigator=make_investigator(client, model, trace_client, rag=rag),
        ask_model=LiveAsk,
        investigation_options=lambda data: data.model_dump(exclude={"question", "remember"}),
        provider=provider_name(client),
        session_cookie=session_cookie,
    )

    from fastapi import Depends

    from relay.models import Actor

    from .streaming_reference import install_streaming

    install_streaming(app)

    @app.get("/api/v1/assistant/capabilities", tags=["Assistant"])
    def capabilities(actor: Actor = Depends(app.state.authorize)):
        return {
            "provider": provider_name(client),
            "memory_modes": ["stateless", "case"],
            "execution_modes": ["workflow", "agent"],
            "runtimes": ["direct", "langgraph"],
            "streaming": "provider deltas consumed; progress then validated result",
            "tracing": "nested execution observations; payloads excluded",
            "retrieval": rag.config.mode if rag else "explicit lexical test adapter",
        }

    if rag is not None:
        from contextlib import asynccontextmanager

        from fastapi import Depends

        from relay.models import Actor
        from relay.service import Problem, require_writer

        @asynccontextmanager
        async def lifespan(app):
            try:
                yield
            finally:
                rag.close()

        app.router.lifespan_context = lifespan
        app.state.rag = rag

        @app.get("/api/v1/rag/status", tags=["RAG"])
        def rag_status(actor: Actor = Depends(app.state.authorize)):
            # No provider call. Exposes only index settings, never unauthorized source IDs.
            try:
                manifest = rag.manifest()
                return {
                    "ready": True,
                    "settings": manifest["settings"],
                    "revision": manifest["revision"],
                    "mode": rag.config.mode,
                    "threshold_calibrated": False,
                }
            except RagFailure as error:
                return {"ready": False, "reason": error.args[0]}

        @app.post("/api/v1/rag/search", tags=["RAG"])
        def rag_search(body: RagQuery, actor: Actor = Depends(app.state.authorize)):
            require_writer(actor)
            try:
                hits, trace = rag.search(app.state.store.documents(actor), body.question, actor)
                return {
                    "hits": [
                        {
                            k: h[k]
                            for k in (
                                "id",
                                "title",
                                "version",
                                "chunk_id",
                                "excerpt",
                                "start",
                                "end",
                                "score",
                                "vector_score",
                            )
                        }
                        for h in hits
                    ],
                    "trace": trace,
                }
            except (RagFailure, OpenAIError):
                raise Problem(
                    503, "rag_unavailable", "Check the vector index and provider configuration."
                ) from None

    return app
