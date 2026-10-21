"""Explicit billable embedding/index preparation for the synthetic C1 corpus."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relay.store import Store  # noqa: E402
from teaching.rag_reference import VectorRag  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["team", "supervisor"], default="supervisor")
    args = parser.parse_args()
    client, _ = live_client()
    rag = VectorRag(client)
    try:
        # A disposable seed store; no owner's cases/history/customer records are indexed.
        with tempfile.TemporaryDirectory(prefix="relay-index-") as temp:
            store = Store(Path(temp) / "seed.sqlite")
            _, actor = store.create_session("supervisor" if args.scope == "supervisor" else "agent")
            report = rag.build(store.documents(actor))
        print(json.dumps(report, indent=2))
    finally:
        rag.close()
        client.close()


if __name__ == "__main__":
    main()
