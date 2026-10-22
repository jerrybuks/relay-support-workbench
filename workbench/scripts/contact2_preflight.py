"""Explicit bounded provider preflight using only disposable original synthetic data."""

import argparse
import json
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from teaching.contact2_app import create_app  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402

QUESTION = (
    "How long can a parcel stay at a collection point, when does that period start, "
    "and who reviews return to the sender?"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-billable", action="store_true")
    args = parser.parse_args()
    if not args.confirm_billable:
        raise SystemExit("Provider preflight requires --confirm-billable.")
    sdk, model = live_client()
    report = {
        "mode": "live-OpenRouter" if "openrouter" in str(sdk.base_url) else "live-OpenAI",
        "date": datetime.now(UTC).isoformat(),
        "model": model,
        "checks": {},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="relay-c2-live-") as directory:
            app = create_app(
                Path(directory) / "app.sqlite",
                client=sdk,
                model=model,
                vector_path=Path(directory) / "vectors",
                state="reference",
            )
            rag = app.state.rag
            report["initial_index"] = rag.build(app.state.store.corpus())
            with TestClient(app, base_url="http://127.0.0.1") as browser:
                session = browser.post("/api/v1/demo/session", json={"role": "supervisor"}).json()
                browser.headers["X-CSRF-Token"] = session["csrf_token"]
                before = browser.post(
                    "/api/v1/cases/RY-1042/investigations",
                    json={"question": QUESTION, "remember": False},
                )
                assert before.status_code == 200
                assert before.json()["status"] == "insufficient_evidence"
                report["before"] = before.json()
                count = rag.embedding_calls
                for document in ["unreviewed.md", "injection.md", "missing-metadata.md"]:
                    rejected = browser.post(
                        "/api/v1/teaching/policies", json={"document": document}
                    )
                    assert rejected.status_code in {403, 422}
                    report["checks"][document] = rejected.json()["error"]["code"]
                assert rag.embedding_calls == count
                report["checks"]["invalid_input_embedding_calls"] = 0
                imports = []
                for document in [
                    "collection.md",
                    "collection.md",
                    "redelivery.md",
                    "restricted.md",
                ]:
                    result = browser.post(
                        "/api/v1/teaching/policies",
                        json={"document": document, "execute": True, "confirm_billable": True},
                    )
                    assert result.status_code == 200, result.status_code
                    imports.append(result.json())
                assert imports[1]["embedding_calls"] == 0 and imports[1]["unchanged"]
                report["imports"] = imports
                session = browser.post("/api/v1/demo/session", json={"role": "agent"}).json()
                browser.headers["X-CSRF-Token"] = session["csrf_token"]
                search = browser.post("/api/v1/rag/search", json={"question": QUESTION}).json()
                assert any(h["id"] == "POL-COLLECTION-1" for h in search["hits"])
                report["retrieval"] = search
                private = browser.post(
                    "/api/v1/rag/search",
                    json={"question": "COLLECTION-REVIEW-7 supervisor collection escalation"},
                ).json()
                assert not any(h["id"] == "POL-ESCALATION-2" for h in private["hits"])
                report["checks"]["restricted_source_absent"] = True
                answer = browser.post(
                    "/api/v1/cases/RY-1042/investigations",
                    json={"question": QUESTION, "remember": False},
                ).json()
                report["answer"] = answer
                run = answer.get("investigation", answer)
                assert run["status"] == "supported", run.get("trace", {}).get("failure")
                assert re.search(r"seven|\b7\b", run["answer"], re.I)
                assert any(c["id"] == "POL-COLLECTION-1" for c in run["citations"])
                assert "notice" in run["answer"].lower() and "supervisor" in run["answer"].lower()
                report["status"] = "passed"
    finally:
        sdk.close()
        target = ROOT / ".runtime/contact2/evidence/live.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {"status": report.get("status"), "mode": report["mode"], "checks": report["checks"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
