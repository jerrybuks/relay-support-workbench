"""Exercise the installed OpenAI SDK against an HTTP mock, with no network/API key."""

import json

import httpx
import pytest


def test_actual_openai_sdk_structured_parse():
    openai = pytest.importorskip("openai", reason="Install references extra for SDK transport test")
    from relay.seed import DOCUMENTS
    from teaching.responses_reference import grounded_response

    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp_fixture",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": "configured-model",
                "output": [
                    {
                        "id": "msg_fixture",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "status": "supported",
                                        "answer": "A reviewed policy applies.",
                                        "cited_ids": ["POL-DELIVERY-3"],
                                    }
                                ),
                                "annotations": [],
                            }
                        ],
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = openai.OpenAI(api_key="local-test-placeholder", http_client=http, max_retries=0)
        result = grounded_response(client, "configured-model", "credit?", [DOCUMENTS[0]])
    assert result["status"] == "supported"
    assert seen[0]["text"]["format"]["type"] == "json_schema"
    assert seen[0]["store"] is False
