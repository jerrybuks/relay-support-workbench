"""Integrated Contact 1 capabilities, actual SDK transports and redacted trace hierarchy."""

import json
from contextlib import contextmanager

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient
from openai import OpenAI
from test_contact1_live import response

from teaching.contact1_live import create_app
from teaching.contact1_reference import search_reference


@pytest.fixture(params=["openai", "openrouter"])
def runtime_client(tmp_path, request):
    requests = []
    controls = {}

    def message(text):
        return {
            "id": "msg_runtime",
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "annotations": [], "text": text}],
        }

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if controls.get("entered") is not None:
            controls["entered"].set()
            controls["release"].wait(timeout=3)
        current = json.loads(
            next(
                x["content"]
                for x in reversed(body["input"])
                if isinstance(x, dict) and x.get("role") == "user"
            )
        )
        if "tools" in body:
            if body["tool_choice"] == "auto":
                if controls.get("loop_forever"):
                    return response(
                        [
                            {
                                "id": "fc_loop",
                                "type": "function_call",
                                "call_id": "loop",
                                "name": "get_shipment",
                                "status": "completed",
                                "arguments": json.dumps({"shipment_id": current["shipment_id"]}),
                            }
                        ]
                    )
                if not any(
                    t.get("name") == "read_policy_chunk" for t in controls.get("executed", [])
                ):
                    controls["executed"] = [{"name": "read_policy_chunk"}]
                    return response(
                        [
                            {
                                "id": "fc_policy",
                                "type": "function_call",
                                "call_id": "policy",
                                "name": "read_policy_chunk",
                                "status": "completed",
                                "arguments": json.dumps({"chunk_id": current["evidence"][0]["id"]}),
                            }
                        ]
                    )
                return response([message("Ready to answer.")])
            return response(
                [
                    {
                        "id": "fc_case",
                        "type": "function_call",
                        "call_id": "case",
                        "name": "get_shipment",
                        "status": "completed",
                        "arguments": json.dumps({"shipment_id": current["shipment_id"]}),
                    }
                ]
            )
        text = json.dumps(
            {
                "status": "supported",
                "answer": "A supervisor must review the credit.",
                "cited_ids": [
                    "OTHER-POL" if controls.get("bad_citation") else current["evidence"][0]["id"]
                ],
            }
        )
        output = message(text)
        final = response([output]).json()
        if body.get("stream"):
            created = {**final, "status": "in_progress", "output": [], "usage": None}
            events = [
                ("response.created", {"response": created}),
                (
                    "response.output_item.added",
                    {"output_index": 0, "item": {**output, "status": "in_progress", "content": []}},
                ),
                (
                    "response.content_part.added",
                    {
                        "output_index": 0,
                        "content_index": 0,
                        "item_id": output["id"],
                        "part": {"type": "output_text", "text": "", "annotations": []},
                    },
                ),
                (
                    "response.output_text.delta",
                    {"output_index": 0, "content_index": 0, "item_id": output["id"], "delta": text},
                ),
                (
                    "response.output_text.done",
                    {"output_index": 0, "content_index": 0, "item_id": output["id"], "text": text},
                ),
                (
                    "response.content_part.done",
                    {
                        "output_index": 0,
                        "content_index": 0,
                        "item_id": output["id"],
                        "part": output["content"][0],
                    },
                ),
                ("response.output_item.done", {"output_index": 0, "item": output}),
                ("response.completed", {"response": final}),
            ]
            data = "".join(
                f"event: {name}\ndata: "
                + json.dumps({"type": name, "sequence_number": i, **value})
                + "\n\n"
                for i, (name, value) in enumerate(events)
            )
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=data)
        return httpx.Response(200, json=final)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with OpenAI(
            api_key="local-test-placeholder",
            base_url="https://openrouter.ai/api/v1"
            if request.param == "openrouter"
            else "https://api.openai.com/v1",
            http_client=http,
            max_retries=0,
        ) as sdk:
            app = create_app(
                tmp_path / "runtime.sqlite",
                client=sdk,
                model="test-model",
                retriever=search_reference,
            )
            with TestClient(app, base_url="http://localhost") as browser:
                login(browser)
                yield browser, requests, controls, app


def ask(browser, question="delivery service credit policy", **options):
    return browser.post(
        "/api/v1/cases/RY-1042/investigations", json={"question": question, **options}
    )


def test_real_conversation_continuity_opt_in_deletion_and_case_isolation(runtime_client):
    browser, requests, _, _ = runtime_client
    assert ask(browser, "FIRST-EXCHANGE delivery credit policy").json()["status"] == "supported"
    assert ask(browser, memory_mode="case").json()["trace"]["memory_exchanges"] == 1
    assert "FIRST-EXCHANGE" in str(requests[-2]["input"][:-1])
    assert ask(browser).json()["trace"]["memory_exchanges"] == 0
    assert "FIRST-EXCHANGE" not in str(requests[-2]["input"])
    assert browser.delete("/api/v1/cases/RY-1042/memory").status_code == 200
    assert ask(browser, memory_mode="case", remember=False).json()["trace"]["memory_exchanges"] == 0
    assert ask(browser, memory_mode="case", remember=False).json()["trace"]["memory_exchanges"] == 0
    assert browser.get("/api/v1/cases/RY-1042").json()["messages"] == []


def test_memory_role_scope_stale_sources_and_context_budget(runtime_client):
    browser, requests, _, app = runtime_client
    login(browser, "supervisor")
    assert ask(browser, "SUPERVISOR-PRIVATE delivery credit policy").json()["status"] == "supported"
    login(browser, "agent")
    assert ask(browser, memory_mode="case").json()["trace"]["memory_exchanges"] == 0
    assert "SUPERVISOR-PRIVATE" not in str(requests[-2:])
    for _ in range(5):
        assert ask(browser, memory_mode="case").json()["status"] == "supported"
    trace = ask(browser, memory_mode="case").json()["trace"]
    assert trace["memory_exchanges"] == 3 and trace["memory_truncated"]
    documents = app.state.store.documents
    app.state.store.documents = lambda actor: [
        {**d, "version": "updated"} for d in documents(actor)
    ]
    trace = ask(browser, memory_mode="case").json()["trace"]
    assert trace["memory_exchanges"] == 0 and trace["memory_skipped_stale_or_unsupported"] > 0


@pytest.mark.parametrize("runtime", ["direct", "langgraph"])
def test_agent_loop_runs_scoped_tools_in_real_app_and_graph(runtime_client, runtime):
    browser, requests, _, _ = runtime_client
    run = ask(browser, execution_mode="agent", runtime=runtime).json()
    assert run["status"] == "supported"
    assert run["trace"]["runtime"] == runtime
    assert run["trace"]["model_calls"] == len(requests) == 4
    assert [t["name"] for t in run["tools"]] == [
        "search_policies",
        "get_shipment",
        "read_policy_chunk",
    ]
    assert run["suggested_credit_naira"] == 2000
    assert browser.get("/api/v1/cases/RY-1042").json()["proposals"] == []


def test_agent_loop_exhaustion_never_generates_or_proposes(runtime_client):
    browser, requests, controls, _ = runtime_client
    controls["loop_forever"] = True
    run = ask(browser, execution_mode="agent").json()
    assert run["status"] == "unavailable" and run["trace"]["failure"] == "agent_turn_budget"
    assert len(requests) == 3 and all("tools" in body for body in requests)
    assert run["citations"] == [] and run["suggested_credit_naira"] is None


@pytest.mark.parametrize("bad_citation", [False, True])
def test_actual_sdk_provider_streams_then_validates_before_saving(runtime_client, bad_citation):
    browser, requests, controls, _ = runtime_client
    controls["bad_citation"] = bad_citation
    result = browser.post(
        "/api/v1/cases/RY-1042/runs/stream",
        json={"question": "delivery service credit policy", "remember": True},
    )
    assert result.status_code == 200
    assert "event: generation_progress" in result.text
    assert "event: completed" in result.text
    assert '"validated": false' in result.text
    completed = json.loads(result.text.split("event: completed\ndata: ", 1)[1].split("\n\n", 1)[0])
    assert completed["status"] == ("unavailable" if bad_citation else "supported")
    assert requests[-1]["stream"] is True
    assert completed["trace"]["streamed"]
    saved = browser.get("/api/v1/cases/RY-1042").json()["messages"]
    assert len(saved) == 1
    assert saved[0]["answer"]["status"] == completed["status"]
    # Progress contains counts, not unvalidated provider text or citation IDs.
    progress = result.text.split("event: generation_progress\ndata: ", 1)[1].split("\n\n", 1)[0]
    assert "supervisor" not in progress and "OTHER-POL" not in progress


def test_stage_telemetry_is_nested_redacted_and_collector_failure_isolated(tmp_path):
    from test_contact1_live import reference

    events = []
    stack = []

    class Collector:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            name = kwargs["name"]
            events.append({"name": name, "parent": stack[-1] if stack else None, **kwargs})
            stack.append(name)
            try:
                yield self
            finally:
                stack.pop()

        def update(self, **kwargs):
            events.append(kwargs)

    with reference(tmp_path, trace_client=Collector()) as (browser, _, _):
        run = ask(browser, "PRIVATE-QUERY delivery credit policy").json()
    assert run["status"] == "supported" and run["trace"]["export"].startswith("submitted")
    stages = {e["name"]: e for e in events if "name" in e}
    assert stages["answer_generation"]["parent"] == "relay.investigation"
    assert stages["get_shipment"]["parent"] == "tool_workflow"
    assert "PRIVATE-QUERY" not in str(events) and "delivery fee" not in str(events)
    assert all(s["duration_ms"] >= 0 for s in run["trace"]["stages"])


def test_unknown_runtime_and_observer_cannot_spend(runtime_client):
    browser, requests, _, _ = runtime_client
    assert ask(browser, runtime="uncontrolled").status_code == 422
    login(browser, "observer")
    assert ask(browser, memory_mode="case").status_code == 403
    assert (
        browser.post(
            "/api/v1/cases/RY-1042/runs/stream", json={"question": "credit policy"}
        ).status_code
        == 403
    )
    assert requests == []


def test_actual_langfuse_sdk_emits_parented_spans_without_network(tmp_path):
    from langfuse import Langfuse
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from test_contact1_live import reference

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    remote_calls = []

    def reject(request):
        remote_calls.append(str(request.url))
        raise AssertionError("No hosted export during local instrumentation test")

    with httpx.Client(transport=httpx.MockTransport(reject)) as http:
        collector = Langfuse(
            public_key="local-test-public",
            secret_key="local-test-secret",
            base_url="http://localhost:9999",
            tracer_provider=provider,
            span_exporter=exporter,
            httpx_client=http,
        )
        try:
            with reference(tmp_path, trace_client=collector) as (browser, _, _):
                run = ask(browser, "PRIVATE-INPUT delivery credit policy").json()
            collector.flush()
            spans = exporter.get_finished_spans()
            by_name = {span.name: span for span in spans}
            assert (
                by_name["answer_generation"].parent.span_id
                == by_name["relay.investigation"].context.span_id
            )
            assert (
                by_name["get_shipment"].parent.span_id == by_name["tool_workflow"].context.span_id
            )
            assert format(by_name["relay.investigation"].context.trace_id, "032x") == run["id"]
            attributes = str([dict(s.attributes) for s in spans])
            assert "PRIVATE-INPUT" not in attributes
            assert "synthetic-kora-1" in attributes
            assert run["trace"]["prompt_version"] in attributes
            assert remote_calls == []
        finally:
            collector.shutdown()
            provider.shutdown()


def test_stream_cancellation_stops_next_call_and_does_not_save_partial_answer(runtime_client):
    import asyncio
    import threading

    from teaching.agent_harness import LiveAsk

    browser, requests, controls, app = runtime_client
    controls.update(entered=threading.Event(), release=threading.Event())
    finished = threading.Event()
    original = app.state.run_query

    def wrapped(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        finally:
            finished.set()

    app.state.run_query = wrapped
    actor = app.state.store.session(browser.cookies.get(app.state.session_cookie))
    endpoint = next(
        route.endpoint
        for route in app.routes
        if getattr(route, "path", None) == "/api/v1/cases/{case_id}/runs/stream"
    )

    async def cancel():
        stream = endpoint("RY-1042", LiveAsk(question="delivery service credit policy"), actor)
        assert "event: started" in await stream.body_iterator.__anext__()
        assert await asyncio.to_thread(controls["entered"].wait, 2)
        await stream.body_iterator.aclose()
        controls["release"].set()
        assert await asyncio.to_thread(finished.wait, 2)

    asyncio.run(cancel())
    assert len(requests) == 1
    assert app.state.store.messages(actor, "RY-1042") == []


def test_model_controls_are_explicit_and_reflected_in_requests(runtime_client, monkeypatch):
    browser, requests, _, _ = runtime_client
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "low")
    monkeypatch.setenv("OPENAI_VERBOSITY", "low")
    monkeypatch.setenv("OPENAI_PROMPT_CACHE_KEY", "relay-local-test")
    run = ask(browser).json()
    assert run["status"] == "supported"
    assert requests[0]["reasoning"] == {"effort": "low"}
    assert requests[1]["text"]["verbosity"] == "low"
    assert requests[1]["text"]["format"]["type"] == "json_schema"
    assert run["trace"]["cached_input_tokens"] == 0
