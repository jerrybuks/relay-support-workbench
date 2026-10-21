"""Hosted class boundaries, with disposable storage and no live credentials."""

import pytest
from conftest import login
from fastapi.testclient import TestClient

from relay.main import create_app

ORIGIN = "https://class.example"
CASE = "/api/v1/cases/RY-1042"


@pytest.fixture
def hosted(monkeypatch, tmp_path):
    monkeypatch.setenv("RELAY_ENV", "workshop")
    monkeypatch.setenv("RELAY_PUBLIC_ORIGIN", ORIGIN)
    monkeypatch.setenv("RELAY_WORKSHOP_DAILY_RUN_LIMIT", "2")
    return create_app(tmp_path / "class.sqlite")


def browser(app):
    client = TestClient(app, base_url=ORIGIN)
    return client


@pytest.mark.parametrize("path", ["/", "/course", "/docs", "/static/app.js", "/api/health"])
def test_public_workshop_has_no_password_gate_but_checks_host(hosted, path):
    with browser(hosted) as client:
        assert client.get(path).status_code == 200
        assert client.get(path, headers={"Host": "evil.example"}).status_code == 403
        assert client.get("/api/v1/cases").status_code == 401
        assert client.get("/api/health", headers={"Host": "127.0.0.1:8000"}).status_code == 200


def test_hosted_sessions_csrf_and_approval_still_enforced(hosted):
    with browser(hosted) as client:
        session = login(client)
        assert session["mode"] == "hosted-workshop"
        response = client.get("/api/v1/session")
        assert response.json()["mode"] == "hosted-workshop"
        response = client.post("/api/v1/demo/session", json={"role": "agent"})
        cookie = response.headers["set-cookie"].lower()
        assert "secure" in cookie and "httponly" in cookie and "samesite=strict" in cookie
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        assert client.get("/api/v1/cases/OTHER-1").status_code == 404
        assert all(
            d["visibility"] == "team" for d in client.get("/api/v1/knowledge").json()["items"]
        )
        body = {"question": "delivery credit policy"}
        assert (
            client.post(
                CASE + "/investigations", json=body, headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                CASE + "/investigations", json=body, headers={"X-CSRF-Token": "wrong"}
            ).status_code
            == 403
        )
        result = client.post(CASE + "/investigations", json=body, headers={"Origin": ORIGIN})
        assert result.status_code == 200 and result.json()["suggested_credit_naira"] == 2000
        proposal = client.post(
            CASE + "/proposals",
            headers={"Idempotency-Key": "class-proposal"},
            json={
                "amount_naira": 2000,
                "rationale": "Delayed express shipment within the policy limit.",
                "case_version": 1,
            },
        )
        assert proposal.status_code == 200
        decision = "/api/v1/proposals/" + proposal.json()["id"] + "/decision"
        assert (
            client.post(
                decision,
                headers={"Idempotency-Key": "class-decision"},
                json={"decision": "approve", "reason": "Policy reviewed."},
            ).status_code
            == 403
        )
        login(client, "supervisor")
        approved = client.post(
            decision,
            headers={"Idempotency-Key": "class-decision"},
            json={"decision": "approve", "reason": "Policy reviewed."},
        )
        assert approved.status_code == 200
        assert (
            client.post(
                decision,
                headers={"Idempotency-Key": "class-decision"},
                json={"decision": "approve", "reason": "Policy reviewed."},
            ).json()
            == approved.json()
        )


def test_request_budget_shared_between_browsers_and_does_not_block_reading(hosted):
    with browser(hosted) as first, browser(hosted) as second:
        login(first)
        login(second)
        body = {"question": "delivery credit policy"}
        assert first.post(CASE + "/investigations", json=body).status_code == 200
        assert second.post(CASE + "/investigations/stream", json=body).status_code == 200
        result = first.post(CASE + "/investigations", json=body)
        assert result.status_code == 429 and result.json()["error"]["code"] == "workshop_run_limit"
        assert first.get(CASE).status_code == 200
        # A fresh day grants a fresh budget. A process restart also resets this ephemeral guard.
        hosted.state.hosting._day = "2000-01-01"
        assert second.post(CASE + "/investigations", json=body).status_code == 200


def test_observer_cannot_use_ai_and_hosted_quota_does_not_replace_role_checks(hosted):
    with browser(hosted) as client:
        login(client, "observer")
        assert (
            client.post(CASE + "/investigations", json={"question": "credit policy"}).status_code
            == 403
        )
        assert hosted.state.hosting._used == 0


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "http://class.example",
        "https://localhost",
        "https://class.example/path",
        "https://user:pass@class.example",
        "https://class.example?key=bad",
    ],
)
def test_workshop_requires_valid_https_origin(monkeypatch, tmp_path, origin):
    monkeypatch.setenv("RELAY_ENV", "workshop")
    monkeypatch.setenv("RELAY_PUBLIC_ORIGIN", origin)
    with pytest.raises(RuntimeError, match="HTTPS"):
        create_app(tmp_path / "invalid.sqlite")


def test_render_origin_is_detected_without_password(monkeypatch, tmp_path):
    monkeypatch.setenv("RELAY_ENV", "workshop")
    monkeypatch.delenv("RELAY_PUBLIC_ORIGIN", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", ORIGIN)
    assert create_app(tmp_path / "valid.sqlite").state.hosting.origin == ORIGIN


def test_shared_minute_limit_is_independent_of_workspace(hosted):
    hosted.state.hosting.minute_limit = 1
    with browser(hosted) as first, browser(hosted) as second:
        login(first)
        login(second)
        body = {"question": "delivery credit policy"}
        assert first.post(CASE + "/investigations", json=body).status_code == 200
        assert second.post(CASE + "/investigations", json=body).status_code == 429
        hosted.state.hosting._minute = -1
        assert second.post(CASE + "/investigations", json=body).status_code == 200


def test_hosted_fixture_entrypoint_uses_new_storage_without_live_imports(monkeypatch, tmp_path):
    from scripts.serve_workshop import create_app as workshop

    monkeypatch.setenv("RELAY_ENV", "workshop")
    monkeypatch.setenv("RELAY_PUBLIC_ORIGIN", ORIGIN)
    monkeypatch.setenv("RELAY_PROFILE", "fixture")
    monkeypatch.setenv("RELAY_DATA_DIR", str(tmp_path / "new-storage"))
    with browser(workshop()) as client:
        assert client.get("/api/health").json()["provider"] == "fixture"
        assert client.get("/").status_code == 200
