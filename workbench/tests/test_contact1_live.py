"""Full API → actual OpenAI SDK → mock HTTP → tool → schema → persistence journey.

No network, generated-quality score, billable tokens or hosted trace claim.
"""

import json
from contextlib import contextmanager

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient

openai = pytest.importorskip("openai")

from teaching.contact1_live import create_app  # noqa: E402
from teaching.contact1_reference import search_reference  # noqa: E402


def response(output, status="completed"):
    return httpx.Response(
        200,
        json={
            "id": "resp_mock",
            "object": "response",
            "created_at": 1,
            "status": status,
            "model": "test-model",
            "output": output,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 25,
                "total_tokens": 125,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        },
    )


@contextmanager
def reference(tmp_path, failure=None, trace_client=None, provider="openai"):
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if failure == "timeout":
            raise httpx.ReadTimeout("PRIVATE-PAYLOAD", request=request)
        if "tools" in body:
            calls = [
                {
                    "type": "function_call",
                    "id": "fc_mock",
                    "call_id": "call_mock",
                    "name": "get_shipment",
                    "arguments": json.dumps(
                        {
                            "shipment_id": "OTHER-1" if failure == "scope" else "KD-80421",
                        }
                    ),
                    "status": "completed",
                }
            ]
            if failure == "budget":
                calls *= 2
            return response(calls, "incomplete" if failure == "incomplete" else "completed")
        if failure == "refusal":
            content = [{"type": "refusal", "refusal": "Unable to answer"}]
        else:
            content = [
                {
                    "type": "output_text",
                    "annotations": [],
                    "text": json.dumps(
                        {
                            "status": "supported",
                            "answer": "A supervisor must review any service credit.",
                            "cited_ids": [
                                "OTHER-POL" if failure == "citation" else "POL-DELIVERY-3"
                            ],
                        }
                    ),
                }
            ]
        return response(
            [
                {
                    "id": "msg_mock",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": content,
                }
            ]
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        sdk = openai.OpenAI(
            api_key="local-test-placeholder",
            http_client=http,
            max_retries=0,
            base_url="https://openrouter.ai/api/v1"
            if provider == "openrouter"
            else "https://api.openai.com/v1",
        )
        app = create_app(
            tmp_path / "c1-live.sqlite",
            client=sdk,
            model="test-model",
            trace_client=trace_client,
            retriever=search_reference,
        )
        with TestClient(app, base_url="http://localhost") as browser:
            login(browser)
            yield browser, requests, app


def ask(browser, question="My parcel arrived overdue, any goodwill?"):
    return browser.post("/api/v1/cases/RY-1042/investigations", json={"question": question})


@pytest.mark.parametrize("provider", ["openai", "openrouter"])
def test_integrated_reference_contract_and_authority(tmp_path, provider):
    with reference(tmp_path, provider=provider) as (browser, requests, app):
        assert browser.get("/api/health").json()["provider"] == provider
        assert browser.get("/api/v1/session").json()["provider"] == provider
        run = ask(browser).json()
        assert run["provider"] == provider and run["status"] == "supported"
        assert run["suggested_credit_naira"] == 2000
        assert run["citations"][0]["excerpt"].startswith("For an express shipment")
        assert len(requests) == run["trace"]["model_calls"] == 2
        assert run["trace"]["input_tokens"] == 200  # Mock usage, never a live measurement.
        assert run["trace"]["api_cost_usd"] is None
        assert all(r["store"] is False and r["max_output_tokens"] == 1800 for r in requests)
        assert requests[0]["tool_choice"]["name"] == "get_shipment"
        assert requests[1]["text"]["format"]["type"] == "json_schema"
        assert requests[1]["input"][-1]["call_id"] == "call_mock"
        assert "Zainab" not in str(requests)
        assert "CANARY" not in str(requests)
        saved = browser.get("/api/v1/cases/RY-1042").json()
        assert saved["messages"][0]["answer"]["provider"] == provider
        assert saved["proposals"] == []  # Model output never creates a business action.
        assert browser.cookies.get("relay_session") is None
        actor = app.state.store.session(browser.cookies.get(app.state.session_cookie))
        assert app.state.store.timeline(actor)[0]["metadata"]["provider"] == provider


@pytest.mark.parametrize(
    "failure", ["scope", "budget", "incomplete", "refusal", "citation", "timeout"]
)
def test_untrusted_or_failed_provider_never_enables_resolution(tmp_path, failure):
    with reference(tmp_path, failure) as (browser, requests, _):
        result = ask(browser)
        assert result.status_code == 200
        run = result.json()
        assert run["status"] == "unavailable"
        assert run["citations"] == [] and run["suggested_credit_naira"] is None
        assert "PRIVATE-PAYLOAD" not in result.text
        assert len(requests) <= 2
        assert run["provider"] == "openai"  # No silent fixture fallback.


def test_no_evidence_avoids_model_and_observer_cannot_invoke(tmp_path):
    with reference(tmp_path) as (browser, requests, _):
        assert (
            ask(browser, "Show confidential reserve reconciliation").json()["status"]
            == "insufficient_evidence"
        )
        assert requests == []
        login(browser, "observer")
        assert ask(browser).status_code == 403
        assert requests == []


def test_saved_supervisor_context_is_not_reused_by_agent(tmp_path):
    with reference(tmp_path) as (browser, requests, _):
        login(browser, "supervisor")
        assert (
            ask(browser, "PRIVATE-SUPERVISOR-CONTEXT delivery credit policy").json()["status"]
            == "supported"
        )
        login(browser, "agent")
        assert browser.get("/api/v1/cases/RY-1042").json()["messages"] == []
        assert ask(browser).json()["status"] == "supported"
        assert "PRIVATE-SUPERVISOR-CONTEXT" not in str(requests[-2:])


def test_profiles_keep_distinct_sessions_on_same_loopback_host(tmp_path, app):
    with TestClient(app, base_url="http://localhost") as starter:
        login(starter)
        original = starter.cookies.get("relay_session")
        with reference(tmp_path) as (live, _, _):
            live.cookies.update(starter.cookies)
            login(live, "supervisor")
            starter.cookies.update(live.cookies)
            assert starter.cookies.get("relay_session") == original
            assert starter.get("/api/v1/session").json()["actor"]["role"] == "agent"
            assert live.get("/api/v1/session").json()["actor"]["role"] == "supervisor"


def test_trace_failure_does_not_lose_validated_result(tmp_path):
    class BrokenCollector:
        def start_as_current_observation(self, **kwargs):
            raise RuntimeError("PRIVATE-TRACE-PAYLOAD")

    with reference(tmp_path, trace_client=BrokenCollector()) as (browser, _, _):
        result = ask(browser)
        assert result.json()["status"] == "supported"
        assert result.json()["trace"]["export"] == "failed"
        assert "PRIVATE-TRACE-PAYLOAD" not in result.text


def test_live_evaluation_budget_and_review_are_explicit():
    from types import SimpleNamespace

    from scripts.evaluate_live import evaluate
    from teaching.responses_reference import GroundedAnswer

    requests = []

    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            status="completed",
            usage=None,
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_shipment",
                    arguments='{"shipment_id":"KD-80421"}',
                    call_id="call_budget",
                )
            ],
        )

    def parse(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            status="completed",
            usage=None,
            output_parsed=GroundedAnswer(
                status="supported",
                answer="Review policy.",
                cited_ids=["POL-DELIVERY-3"],
            ),
        )

    client = SimpleNamespace(responses=SimpleNamespace(create=create, parse=parse))
    item = {"id": "budget", "slice": "exact", "question": "delivery service credit policy"}
    report = evaluate(
        client,
        "mock-model",
        {
            "version": "test",
            "review_status": "draft",
            "cases": [item, item],
        },
        max_calls=2,
    )
    assert len(requests) == report["actual_model_calls"] == 2
    assert report["completed_cases"] == 1 and report["total_cases"] == 2
    assert report["semantic_accuracy"] is None
    assert report["outcomes"][0]["semantic_review"]["status"] == "pending-human-review"
