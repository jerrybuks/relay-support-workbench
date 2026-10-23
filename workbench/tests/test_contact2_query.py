"""Direct policy query: actual SDK + local Qdrant, fixture HTTP, no case runtime."""

import json
from dataclasses import replace

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient
from openai import OpenAI
from test_contact1_live import response

from teaching.contact2_app import create_app
from teaching.rag_reference import RagConfig


@pytest.mark.parametrize("outcome", ["supported", "empty", "bad_citation", "timeout"])
def test_direct_query_retrieves_generates_and_validates_without_case_runtime(tmp_path, outcome):
    calls = []

    def handler(request):
        data = json.loads(request.content)
        calls.append((request.url.path, data))
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": "text-embedding-3-small",
                    "data": [
                        {
                            "object": "embedding",
                            "index": i,
                            "embedding": [0.0, 1.0, 0.0]
                            if text == "unrelated quasar"
                            else [1.0, 0.0, 0.0],
                        }
                        for i, text in enumerate(data["input"])
                    ],
                    "usage": {"prompt_tokens": 10, "total_tokens": 10},
                },
            )
        assert request.url.path.endswith("/responses")
        assert not data.get("tools") and not data.get("stream")
        if outcome == "timeout":
            raise httpx.ReadTimeout("PRIVATE_PROVIDER_MESSAGE", request=request)
        content = json.loads(data["input"][1]["content"])
        assert "shipment_id" not in content
        assert "PRIVATE-EMBEDDING-PAYLOAD" not in str(content)
        cited = "invented" if outcome == "bad_citation" else content["evidence"][0]["id"]
        return response(
            [
                {
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "annotations": [],
                            "text": json.dumps(
                                {
                                    "status": "supported",
                                    "answer": "The approved policy applies.",
                                    "cited_ids": [cited],
                                }
                            ),
                        }
                    ],
                }
            ]
        )

    client = OpenAI(
        api_key="fixture",
        base_url="https://api.openai.com/v1",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    config = replace(RagConfig(), dimensions=3, mode="hybrid", min_score=0.8)
    app = create_app(
        tmp_path / "app.sqlite",
        client=client,
        model="test-model",
        vector_path=tmp_path / "vectors",
        rag_config=config,
    )
    try:
        with TestClient(app, base_url="http://127.0.0.1") as browser:
            app.state.rag.build(app.state.store.corpus())
            calls.clear()

            def forbidden_case_runtime(*args, **kwargs):
                raise AssertionError("Policy queries must not call the case investigator")

            app.state.run_query = forbidden_case_runtime
            assert (
                browser.post(
                    "/api/v1/policies/query", json={"question": "delivery policy"}
                ).status_code
                == 401
            )
            login(browser, "observer")
            assert (
                browser.post(
                    "/api/v1/policies/query", json={"question": "delivery policy"}
                ).status_code
                == 403
            )
            login(browser)
            token = browser.headers.pop("X-CSRF-Token")
            assert (
                browser.post(
                    "/api/v1/policies/query", json={"question": "delivery policy"}
                ).status_code
                == 403
            )
            browser.headers["X-CSRF-Token"] = token
            assert browser.post("/api/v1/policies/query", json={"question": "x"}).status_code == 422
            assert calls == []

            question = "unrelated quasar" if outcome == "empty" else "delivery policy"
            result = browser.post("/api/v1/policies/query", json={"question": question})
            if outcome in {"timeout", "bad_citation"}:
                assert result.status_code == 503
                assert result.json()["error"]["code"] == "policy_query_unavailable"
                assert "PRIVATE_PROVIDER_MESSAGE" not in result.text
                return
            assert result.status_code == 200, result.text
            data = result.json()
            if outcome == "empty":
                assert data["status"] == "insufficient_evidence"
                assert not data["citations"] and not data["retrieved_passages"]
                assert data["trace"]["model_calls"] == 0
                assert len(calls) == 1
            else:
                assert data["status"] == "supported"
                assert data["citations"][0] in data["retrieved_passages"]
                assert data["citations"][0]["vector_score"] >= config.min_score
                assert data["trace"]["model_calls"] == 1
                assert [path.rsplit("/", 1)[-1] for path, _ in calls] == ["embeddings", "responses"]
    finally:
        client.close()
