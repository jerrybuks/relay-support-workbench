"""A real API/vector/SDK composition over mock HTTP; not semantic quality evidence."""

import copy
import json

import httpx
from openai import OpenAI
from test_contact1_live import response

from relay.seed import DOCUMENTS
from scripts.contact1_conflict import run_conflict
from teaching.conflict_reference import conflict_documents


def test_conflict_corpus_is_isolated_and_preserves_actor_scope():
    original = copy.deepcopy(DOCUMENTS)
    team = [
        d
        for d in original
        if d["tenant"] == "kora" and d["visibility"] == "team" and d["state"] == "published"
    ]
    changed = conflict_documents(team)
    assert {d["id"] for d in changed} >= {"POL-CONFLICT-A", "POL-CONFLICT-B"}
    assert all(d["tenant"] == "kora" and d["visibility"] == "team" for d in changed)
    assert "POL-DELIVERY-3" not in {d["id"] for d in changed}
    foreign = [d for d in original if d["tenant"] == "other"]
    assert conflict_documents(foreign) == foreign
    assert DOCUMENTS == original


def test_conflict_api_retrieves_both_sources_abstains_and_has_no_business_effect():
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append((request.url.path, body))
        if request.url.path.endswith("embeddings"):
            size = body["dimensions"]

            def embedding(text):
                # Test vectors encode the policy/query match, not learned semantics.
                return (
                    [1.0, 0.0] + [0.0] * (size - 2)
                    if "credit" in text.lower()
                    else [0.0, 1.0] + [0.0] * (size - 2)
                )

            return httpx.Response(
                200,
                json={
                    "data": [
                        {"index": i, "embedding": embedding(t), "object": "embedding"}
                        for i, t in enumerate(body["input"])
                    ],
                    "model": body["model"],
                    "object": "list",
                    "usage": {"prompt_tokens": 10, "total_tokens": 10},
                },
            )
        if "tools" in body:
            return response(
                [
                    {
                        "type": "function_call",
                        "id": "fc_conflict",
                        "call_id": "call_conflict",
                        "name": "get_shipment",
                        "arguments": '{"shipment_id":"KD-80421"}',
                        "status": "completed",
                    }
                ]
            )
        evidence = json.loads(body["input"][1]["content"])["evidence"]
        assert {e["source_id"] for e in evidence} >= {"POL-CONFLICT-A", "POL-CONFLICT-B"}
        return response(
            [
                {
                    "id": "msg_conflict",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "annotations": [],
                            "text": json.dumps(
                                {
                                    "status": "insufficient_evidence",
                                    "answer": (
                                        "The current policies conflict; ask a supervisor "
                                        "to clarify before promising a credit."
                                    ),
                                    "cited_ids": [],
                                }
                            ),
                        }
                    ],
                }
            ]
        )

    with OpenAI(
        api_key="test-placeholder",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        report = run_conflict(client, "test-model")
    assert report["contract_passed"]
    assert report["semantic_review"]["status"] == "pending-facilitator-review"
    assert len([p for p, _ in seen if p.endswith("responses")]) == 2
    assert report["review_status"] == "draft-awaiting-facilitator-review"
