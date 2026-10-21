"""Run one billable conflicting-policy investigation using a disposable API/database/index."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from teaching.conflict_reference import FIXTURE, create_conflict_app, scenario  # noqa: E402
from teaching.provider_connection import provider_name  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402


def run_conflict(client, model):
    fixture = scenario()
    with tempfile.TemporaryDirectory(prefix="relay-conflict-") as temp:
        app = create_conflict_app(
            Path(temp) / "cases.sqlite",
            client=client,
            model=model,
            vector_path=Path(temp) / "vectors",
        )
        with TestClient(app, base_url="http://127.0.0.1:8000") as browser:
            _, supervisor = app.state.store.create_session("supervisor")
            index = app.state.rag.build(app.state.store.documents(supervisor))
            session = browser.post("/api/v1/demo/session", json={"role": "agent"})
            session.raise_for_status()
            browser.headers["X-CSRF-Token"] = session.json()["csrf_token"]
            response = browser.post(
                f"/api/v1/cases/{fixture['case_id']}/investigations",
                json={"question": fixture["question"]},
            )
            response.raise_for_status()
            result = response.json()
            state = browser.get(f"/api/v1/cases/{fixture['case_id']}").json()
        retrieved = {h["id"] for h in result["trace"].get("retrieved_chunks", [])}
        expected_ids = {p["id"] for p in fixture["policies"]}
        checks = {
            "both_conflicting_sources_retrieved": expected_ids <= retrieved,
            "abstained": result["status"] == "insufficient_evidence",
            "no_claimed_support": result["citations"] == [],
            "no_suggested_credit": result["suggested_credit_naira"] is None,
            "no_proposals_created": state["proposals"] == [],
        }
        return {
            "provider": provider_name(client),
            "model": model,
            "scenario": fixture["version"],
            "scenario_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            "review_status": fixture["review_status"],
            "checks": checks,
            "contract_passed": all(checks.values()),
            "semantic_review": {
                "status": "pending-facilitator-review",
                "rubric": fixture["expected"]["human_rubric"],
            },
            "index": index,
            "run": result,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".runtime/c1-preparation/conflict.json"
    )
    args = parser.parse_args()
    client, model = live_client()
    try:
        report = run_conflict(client, model)
    except Exception as exc:
        report = {
            "status": "unavailable",
            "exception_type": type(exc).__name__,
            "http_status": getattr(exc, "status_code", None),
        }
    finally:
        client.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "provider",
                    "model",
                    "checks",
                    "contract_passed",
                    "status",
                    "exception_type",
                    "http_status",
                )
                if k in report
            },
            indent=2,
        )
    )
    return 0 if report.get("contract_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
