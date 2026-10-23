"""Contact 2 commands. Owner Contact 1 data is never read, reset or indexed."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relay.service import Problem  # noqa: E402
from teaching.contact2 import exercise, parser_reference  # noqa: E402
from teaching.contact2.markdown_practice import preview  # noqa: E402
from teaching.contact2.policy_store import PolicyStore  # noqa: E402
from teaching.contact2.policy_store import publish_source as ingest  # noqa: E402
from teaching.rag_reference import RagConfig, VectorRag  # noqa: E402


def home():
    return Path(os.getenv("RELAY_C2_HOME", str(ROOT / ".runtime/contact2")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["preview", "init", "ingest", "serve", "check"])
    parser.add_argument("--state", choices=["before", "reference"], default="before")
    parser.add_argument("--document", default="collection.md")
    parser.add_argument("--confirm-billable", action="store_true")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    parse = exercise.parse_markdown if args.state == "before" else parser_reference.parse_markdown
    if args.command == "check":
        # Acceptance check intentionally red before; no provider calls.
        from teaching.contact2.acceptance import check

        print(json.dumps({**check(parse), "state": args.state}))
        return
    if args.command == "preview":
        source, passages = preview(args.document, parse, config=RagConfig.environment())
        print(json.dumps({"source": source, "chunks": passages, "embedding_calls": 0}, indent=2))
        return
    if args.command == "serve":
        import uvicorn

        os.environ["RELAY_C2_STATE"] = args.state
        uvicorn.run(
            "teaching.contact2_app:create_app",
            factory=True,
            host="127.0.0.1",
            port=8002,
            reload=args.reload,
            reload_dirs=[str(ROOT / "teaching/contact2")] if args.reload else None,
        )
        return
    if not args.confirm_billable:
        raise SystemExit("init/ingest require --confirm-billable; stop the teaching server first.")
    from teaching.responses_reference import live_client

    # Pre-validate all untrusted input before connecting or spending tokens.
    source = (
        preview(args.document, parse, config=RagConfig.environment())[0]
        if args.command == "ingest"
        else None
    )
    client, _ = live_client()
    rag = None
    try:
        store = PolicyStore(home() / "workshop.sqlite")
        rag = VectorRag(client, home() / "vectors")
        if source:
            _, actor = store.create_session("supervisor")
            report = ingest(store, rag, source, actor)
        else:
            report = rag.build(store.corpus())
        print(json.dumps(report, indent=2))
    finally:
        if rag is not None:
            rag.close()
        client.close()


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError:
        print("EXPECTED BEFORE FAILURE: implement teaching/contact2/exercise.py", file=sys.stderr)
        raise SystemExit(1) from None
    except Problem as error:
        print(json.dumps({"error": error.code, "message": error.message}), file=sys.stderr)
        raise SystemExit(1) from None
