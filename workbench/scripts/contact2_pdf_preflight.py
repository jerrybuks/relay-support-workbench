"""Explicit, billable PDF-to-answer smoke on original synthetic data and disposable stores."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-billable", action="store_true")
    args = parser.parse_args()
    if not args.confirm_billable:
        raise SystemExit("Pass --confirm-billable to run real embedding and answer requests.")
    from fastapi.testclient import TestClient

    from teaching.contact2_app import create_app
    from teaching.responses_reference import live_client

    client, model = live_client()
    try:
        with tempfile.TemporaryDirectory(prefix="relay-pdf-preflight-") as tmp:
            app = create_app(
                Path(tmp) / "demo.sqlite",
                client=client,
                model=model,
                vector_path=Path(tmp) / "vectors",
                state="before",
            )
            with TestClient(app, base_url="http://127.0.0.1") as browser:
                session = browser.post("/api/v1/demo/session", json={"role": "supervisor"})
                session.raise_for_status()
                browser.headers["X-CSRF-Token"] = session.json()["csrf_token"]
                raw = (ROOT / "teaching/contact2/pdfs/collection-policy.pdf").read_bytes()
                response = browser.post(
                    "/api/v1/teaching/pdf?title=Parcel%20collection%20and%20return%20policy",
                    content=raw,
                    headers={"Content-Type": "application/pdf"},
                )
                response.raise_for_status()
                staged = response.json()
                base = "/api/v1/teaching/pdf/" + staged["upload_id"]
                browser.post(base + "/review", json={"confirm_reviewed": True}).raise_for_status()
                response = browser.post(base + "/index", json={"confirm_billable": True})
                response.raise_for_status()
                indexed = response.json()
                response = browser.post(
                    "/api/v1/policies/query",
                    json={
                        "question": (
                            "How long can a parcel stay at a collection point, "
                            "when does that period start, and who reviews return to the sender?"
                        ),
                    },
                )
                response.raise_for_status()
                answer = response.json()
                assert answer.get("status") == "supported", answer.get("status")
                assert any(c["id"] == staged["source"]["id"] for c in answer["citations"])
                assert answer["retrieved_passages"]
                response = browser.post(base + "/index", json={"confirm_billable": True})
                response.raise_for_status()
                assert response.json()["embedding_calls"] == 0
                evidence = {
                    "mode": "live-provider-disposable-data",
                    "model": model,
                    "pages": len(staged["pages"]),
                    "policy_chunks": indexed["stored_chunks"],
                    "index_embedding_calls": indexed["embedding_calls"],
                    "dimensions": indexed["records"][0]["dimensions"],
                    "source_id": staged["source"]["id"],
                    "answer": answer["answer"],
                    "citations": answer["citations"],
                    "retrieved_passages": answer["retrieved_passages"],
                    "status": "passed",
                    "repeat_embedding_calls": 0,
                }
                target = ROOT / ".runtime/contact2/evidence/pdf-live.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(evidence, indent=2) + "\n")
                print(
                    json.dumps(
                        {
                            k: v
                            for k, v in evidence.items()
                            if k not in {"answer", "citations", "retrieved_passages"}
                        },
                        indent=2,
                    )
                )
    finally:
        client.close()


if __name__ == "__main__":
    main()
