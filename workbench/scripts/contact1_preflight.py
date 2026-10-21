"""Configuration/readiness inspection; --live explicitly opts into bounded billable smoke."""

import argparse
import importlib.metadata
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relay.store import Store  # noqa: E402
from teaching.investigation_reference import make_investigator  # noqa: E402
from teaching.observability_reference import collector_received  # noqa: E402
from teaching.provider_connection import selected_provider, vector_path  # noqa: E402
from teaching.rag_reference import RagConfig, VectorRag  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402


def configuration():
    prefix = "OPENROUTER" if selected_provider() == "openrouter" else "OPENAI"
    required = (
        (f"{prefix}_API_KEY",) if prefix == "OPENROUTER" else ("OPENAI_API_KEY", "OPENAI_MODEL")
    )
    configured = {name: bool(os.getenv(name)) for name in required}
    configured["RELAY_ALLOW_LIVE"] = os.getenv("RELAY_ALLOW_LIVE") == "1"
    index_path = vector_path()
    return {
        "provider": selected_provider(),
        "configured": configured,
        "index_manifest_present": (index_path / "relay-manifest.json").is_file(),
        "index_query_verified": False,
        "provider_calls": 0,
        "live_smoke": "not-run",
        "langfuse_delivery": "not-run",
        "human_dataset_review": "required",
        "timed_rehearsal": "required",
        "class_ready": False,
        "versions": {
            name: importlib.metadata.version(name)
            for name in (
                "openai",
                "qdrant-client",
                "langfuse",
                "langchain-text-splitters",
                "langgraph",
            )
        },
    }


def live_smoke(report, *, trace=False, scenario="workflow"):
    client, model = live_client()
    collector = None
    rag = None
    try:
        if trace:
            if os.getenv("RELAY_TRACE_EXPORT") != "1" or not all(
                os.getenv(name)
                for name in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
            ):
                raise RuntimeError("Configure explicit Langfuse export and credentials first.")
            from langfuse import Langfuse

            collector = Langfuse(additional_headers={"x-langfuse-ingestion-version": "4"})
        rag = VectorRag(client, config=RagConfig.environment())
        rag.manifest()
        with tempfile.TemporaryDirectory(prefix="relay-preflight-") as temp:
            store = Store(Path(temp) / "cases.sqlite")
            _, actor = store.create_session("agent")
            run = make_investigator(client, model, collector, rag)(
                store,
                actor,
                store.case(actor, "RY-1042"),
                "My parcel arrived overdue, any goodwill?",
                execution_mode="agent" if scenario == "agent" else "workflow",
                runtime="langgraph" if scenario == "langgraph" else "direct",
                stream=scenario == "stream",
            )
        report.update(
            live_smoke="passed" if run["status"] == "supported" else "failed",
            index_query_verified=bool(run["trace"].get("retrieved_chunks")),
            provider_calls=run["trace"]["model_calls"] + run["trace"].get("embedding_calls", 0),
            result={
                "run_id": run["id"],
                "status": run["status"],
                "trace": run["trace"],
                "source_ids": [c["id"] for c in run["citations"]],
            },
        )
        if collector:
            collector.flush()
            report["langfuse_delivery"] = "submitted-not-confirmed"
            for attempt in range(4):
                try:
                    if collector_received(collector, run["id"]):
                        report["langfuse_delivery"] = "confirmed-by-observation-read"
                        break
                except Exception:
                    pass
                if attempt < 3:
                    time.sleep(2)
            # Collector ingestion is asynchronous; flush() alone is not receipt proof.
    finally:
        if rag:
            rag.close()
        if collector:
            collector.shutdown()
        client.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument(
        "--scenario", choices=["workflow", "agent", "langgraph", "stream"], default="workflow"
    )
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/c1-preflight.json")
    args = parser.parse_args()
    if args.trace and not args.live:
        parser.error("--trace requires --live; ordinary inspection makes no network calls.")
    report = configuration()
    if args.live:
        try:
            report = live_smoke(report, trace=args.trace, scenario=args.scenario)
        except Exception:
            # Raw SDK errors can contain headers/payloads; don't print them.
            report["provider_calls"] = None
            report["live_smoke"] = "failed; check credentials/index/service configuration locally"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    success = (
        report["live_smoke"] == "passed"
        if args.live
        else (all(report["configured"].values()) and report["index_manifest_present"])
    )
    if args.trace:
        success = success and report["langfuse_delivery"] == "confirmed-by-observation-read"
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
