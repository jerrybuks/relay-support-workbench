"""Real SDK/mock HTTP comparison: request lineage, state scope and failure cleanup.

These tests prove contracts, never model recall or provider deletion/retention.
"""

import json

import httpx
import pytest
from openai import OpenAI
from test_contact1_live import response

from teaching.openai_state_reference import (
    FIRST,
    FOLLOW_UP,
    INSTRUCTIONS,
    StateComparisonFailure,
    compare_state,
)


@pytest.mark.parametrize("mode", ["stateless", "manual", "previous", "conversation"])
def test_sdk_state_strategies_and_scoped_cleanup(mode):
    requests = []
    generations = []

    def handler(request):
        body = json.loads(request.content) if request.content else None
        requests.append((request.method, request.url.path, body))
        if request.method == "DELETE":
            if "/items/" in request.url.path:
                return httpx.Response(
                    200,
                    json={
                        "id": "conv_synthetic",
                        "object": "conversation",
                        "created_at": 1,
                        "metadata": {},
                    },
                )
            return httpx.Response(
                200,
                json={
                    "id": request.url.path.split("/")[-1],
                    "object": "conversation.deleted"
                    if "/conversations/" in request.url.path
                    else "response",
                    "deleted": True,
                },
            )
        if request.url.path == "/v1/conversations":
            return httpx.Response(
                200,
                json={
                    "id": "conv_synthetic",
                    "object": "conversation",
                    "created_at": 1,
                    "metadata": {},
                },
            )
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {
                            "id": "msg_synthetic",
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": FIRST}],
                        }
                    ],
                    "has_more": False,
                    "first_id": "msg_synthetic",
                    "last_id": "msg_synthetic",
                },
            )
        generations.append(body)
        result = response(
            [
                {
                    "id": f"msg_{len(generations)}",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "annotations": [],
                            "text": "Synthetic fee acknowledgement.",
                        }
                    ],
                }
            ]
        ).json()
        result["id"] = f"resp_{len(generations)}"
        return httpx.Response(200, json=result)

    with OpenAI(
        api_key="test-placeholder",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        report = compare_state(client, "test-model", mode)
    assert report["generation_attempts"] == len(generations) == 2
    assert all(b["instructions"] == INSTRUCTIONS for b in generations)
    second = generations[1]
    assert second["input"][-1]["content"] == FOLLOW_UP
    assert second["store"] == (mode in {"previous", "conversation"})
    if mode == "manual":
        assert second["input"][0]["content"] == FIRST
        assert second["input"][1]["type"] == "message"
        assert "reasoning.encrypted_content" in second["include"]
    else:
        assert len(second["input"]) == 1
    assert second.get("previous_response_id") == ("resp_1" if mode == "previous" else None)
    assert second.get("conversation") == ("conv_synthetic" if mode == "conversation" else None)
    deletes = [path for method, path, _ in requests if method == "DELETE"]
    if mode == "conversation":
        assert deletes[:2] == [
            "/v1/conversations/conv_synthetic/items/msg_synthetic",
            "/v1/conversations/conv_synthetic",
        ]
    if mode in {"previous", "conversation"}:
        assert deletes[-2:] == ["/v1/responses/resp_2", "/v1/responses/resp_1"]
        assert not any("failed" in s for s in report["cleanup"])
    else:
        assert deletes == []


def test_failed_follow_up_attempts_cleanup_without_retry():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(200, json={"id": "resp_first", "deleted": True})
        if len(calls) == 2:
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        data = response(
            [
                {
                    "id": "msg_first",
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "Acknowledged.", "annotations": []}
                    ],
                }
            ]
        ).json()
        data["id"] = "resp_first"
        return httpx.Response(200, json=data)

    with OpenAI(
        api_key="test-placeholder",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        with pytest.raises(StateComparisonFailure, match="State comparison failed"):
            compare_state(client, "test-model", "previous")
    assert calls == [
        ("POST", "/v1/responses"),
        ("POST", "/v1/responses"),
        ("DELETE", "/v1/responses/resp_first"),
    ]
