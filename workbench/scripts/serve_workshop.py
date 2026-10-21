"""Single-process hosted workshop entrypoint; never loaded by baseline startup."""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relay.hosting import Hosting  # noqa: E402


def prepare_index(client):
    from relay.seed import DOCUMENTS
    from teaching.rag_reference import VectorRag

    rag = VectorRag(client)
    try:
        if os.getenv("RELAY_BOOTSTRAP_INDEX") == "1":
            # Explicit hosted opt-in: only original published fictional teaching policies.
            report = rag.build(
                [d for d in DOCUMENTS if d["tenant"] == "kora" and d["state"] == "published"]
            )
            print(
                f"Synthetic policy index ready; {report['embedding_calls']} embedding requests.",
                flush=True,
            )
        else:
            rag.manifest()
    finally:
        rag.close()


def create_app():
    hosting = Hosting()  # Validate hosting settings before any billable index preparation.
    if not hosting.workshop:
        raise RuntimeError("This entrypoint requires RELAY_ENV=workshop.")
    profile = os.getenv("RELAY_PROFILE", "live")
    if profile not in {"fixture", "live"}:
        raise RuntimeError("RELAY_PROFILE must be fixture or live.")
    data = Path(os.getenv("RELAY_DATA_DIR", "/data"))
    data.mkdir(parents=True, exist_ok=True)
    # New hosting data only; never copy the owner's local runtime files into an image.
    os.environ.setdefault("RELAY_REFERENCE_DB", str(data / "workshop.sqlite"))
    os.environ.setdefault("RELAY_VECTOR_PATH", str(data / "vectors"))
    if profile == "fixture":
        from relay.main import create_app as baseline

        return baseline(data / "workshop.sqlite", checkpoint="hosted-workshop-fixture")

    from teaching.contact1_live import create_app as live
    from teaching.responses_reference import live_client

    client, model = live_client()
    trace = None
    try:
        prepare_index(client)
        if os.getenv("RELAY_TRACE_EXPORT") == "1":
            from langfuse import Langfuse

            if not all(
                os.getenv(key)
                for key in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
            ):
                raise RuntimeError("Configure Langfuse before enabling trace export.")
            trace = Langfuse(additional_headers={"x-langfuse-ingestion-version": "4"})
        app = live(client=client, model=model, trace_client=trace)
    except Exception:
        client.close()
        if trace is not None:
            trace.shutdown()
        # SDK/network errors must not print credentials or provider payloads to hosting logs.
        raise RuntimeError(
            "Live workshop startup failed. Check provider credit, credentials and index settings."
        ) from None
    previous = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(app):
        try:
            async with previous(app):
                yield
        finally:
            if trace is not None:
                trace.flush()
                trace.shutdown()
            client.close()

    app.router.lifespan_context = lifespan
    return app


def main():
    import uvicorn

    # Use provider-assigned port. One worker owns SQLite and local Qdrant.
    uvicorn.run(
        create_app(),
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        proxy_headers=True,
        forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        limit_concurrency=32,
    )


if __name__ == "__main__":
    main()
