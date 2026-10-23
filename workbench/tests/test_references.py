import json
from types import SimpleNamespace

import pytest
from conftest import login
from fastapi.testclient import TestClient

from relay.main import create_app
from relay.seed import DOCUMENTS
from teaching.contact1_reference import search_reference
from teaching.idempotency_practice import apply_event_before as broken
from teaching.idempotency_practice import apply_event_reference as fixed
from teaching.ingestion_reference import create_app as ingestion_app
from teaching.responses_reference import GroundedAnswer, grounded_response
from teaching.tool_loop_reference import run_tool_loop


def test_reference_retrieval_preserves_acl_and_finds_paraphrase(tmp_path):
    app = create_app(
        tmp_path / "c1.sqlite", retriever=search_reference, checkpoint="contact-1-reference"
    )
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        response = client.post(
            "/api/v1/cases/RY-1042/investigations",
            json={"question": "My parcel arrived overdue, any goodwill?"},
        )
        assert response.json()["status"] == "supported"
        assert "POL-DELIVERY-3" in [d["id"] for d in response.json()["citations"]]
        assert "CANARY" not in response.text
        assert client.get("/api/health").json()["checkpoint"] == "contact-1-reference"


def fake_client(answer=None, status="completed", output=None):
    response = SimpleNamespace(
        output_parsed=answer,
        status=status,
        usage=None,
        output=output or [],
        output_text="Shipment checked",
    )
    calls = []

    def invoke(**kwargs):
        calls.append(kwargs)
        return response

    return SimpleNamespace(responses=SimpleNamespace(parse=invoke, create=invoke)), calls


def test_responses_schema_and_citation_contract():
    client, calls = fake_client(
        GroundedAnswer(status="supported", answer="Policy guidance", cited_ids=["POL-DELIVERY-3"])
    )
    result = grounded_response(client, "configured-model", "credit?", [DOCUMENTS[0]])
    assert result["citations"][0]["id"] == "POL-DELIVERY-3"
    assert calls[0]["store"] is False
    assert calls[0]["text_format"] is GroundedAnswer
    assert calls[0]["input"][1]["role"] == "user"


@pytest.mark.parametrize("ids", [["made-up"], []])
def test_responses_rejects_invalid_citations(ids):
    client, _ = fake_client(GroundedAnswer(status="supported", answer="Untrusted", cited_ids=ids))
    with pytest.raises(ValueError):
        grounded_response(client, "model", "question", [DOCUMENTS[0]])


def test_refusal_incomplete_and_no_evidence_abstain():
    for status in ["completed", "incomplete"]:
        client, calls = fake_client(None, status)
        assert (
            grounded_response(client, "model", "question", [DOCUMENTS[0]])["status"]
            == "insufficient_evidence"
        )
        calls.clear()
        assert grounded_response(client, "model", "question", [])["model_called"] is False
        assert calls == []


def test_tool_authority_and_loop_budget():
    call = SimpleNamespace(
        type="function_call",
        name="get_shipment",
        call_id="call-1",
        arguments=json.dumps({"shipment_id": "OTHER-1"}),
    )
    client, _ = fake_client(output=[call])
    with pytest.raises(PermissionError):
        run_tool_loop(client, "model", "lookup", {"id": "KD-80421"})
    call.arguments = json.dumps({"shipment_id": "KD-80421"})
    with pytest.raises(RuntimeError, match="budget"):
        run_tool_loop(client, "model", "lookup", {"id": "KD-80421"}, max_turns=2)


def test_contact2_reproduction_and_fix():
    event = {"id": "evt-1", "amount": 2000}
    before, after = [], []
    broken(before, event)
    assert broken(before, event) == 4000
    fixed(after, event)
    assert fixed(after, event) == 2000
    with pytest.raises(ValueError):
        fixed(after, {**event, "amount": 3000})


def test_ingestion_queue_review_and_visibility(tmp_path):
    app = ingestion_app(tmp_path / "review.sqlite")
    with TestClient(app, base_url="http://localhost") as client:
        login(client)
        candidate = {
            "source_id": "POL-FRESHNESS-1",
            "title": "Freshness review policy",
            "html": "<p>Review a published policy whenever its owner changes it.</p>"
            "<script>stealCredentials()</script>",
            "license_notes": "Original synthetic workshop text",
            "provenance": "Facilitator-authored local fixture",
        }
        response = client.post("/api/v1/review/candidates", json=candidate)
        assert response.status_code == 200, response.text
        assert response.json()["reviewed_by"] is None
        assert "stealCredentials" not in response.json()["text"]
        assert "POL-FRESHNESS" not in client.get("/api/v1/knowledge").text
        assert client.post("/api/v1/review/candidates", json=candidate).status_code == 409
        path = "/api/v1/review/candidates/POL-FRESHNESS-1/publish"
        assert client.post(path).status_code == 403
        login(client, "supervisor")
        assert client.post(path).json()["state"] == "published"
        assert "POL-FRESHNESS" in client.get("/api/v1/knowledge").text
        assert client.post(path).status_code == 409


def test_candidate_cannot_supply_approval_or_missing_rights(tmp_path):
    with TestClient(
        ingestion_app(tmp_path / "review.sqlite"), base_url="http://localhost"
    ) as client:
        login(client)
        response = client.post(
            "/api/v1/review/candidates", json={"source_id": "POL-NEW", "reviewed_by": "invented"}
        )
        assert response.status_code == 422


def test_baseline_has_no_reference_routes(app, logged):
    assert logged.post("/api/v1/review/candidates", json={}).status_code == 404
    assert app.state.checkpoint == "m0-baseline"


def test_live_provider_requires_explicit_opt_in(monkeypatch):
    from teaching.responses_reference import live_client

    monkeypatch.delenv("RELAY_ALLOW_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="authorized"):
        live_client()
