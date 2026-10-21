"""Judge schemas, spending isolation, explicit human labels and no-key preflight."""

import json
from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI
from test_contact1_live import response

from scripts.review_evaluation import apply_reviews
from teaching.semantic_evaluation import judge_answer


def test_actual_sdk_judge_validates_rubric_and_uses_separate_budget():
    from scripts.evaluate_live import evaluate

    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if body["model"] == "judge-model":
            text = json.dumps(
                {
                    "claims_supported": False,
                    "no_unauthorized_promise": True,
                    "useful_next_step": True,
                    "rationale": "An answer claim lacks support.",
                    "verdict": "fail",
                }
            )
        elif "tools" in body:
            return response(
                [
                    {
                        "id": "fc_eval",
                        "call_id": "eval",
                        "type": "function_call",
                        "name": "get_shipment",
                        "arguments": '{"shipment_id":"KD-80421"}',
                        "status": "completed",
                    }
                ]
            )
        else:
            text = json.dumps(
                {
                    "status": "supported",
                    "answer": "Review the credit policy.",
                    "cited_ids": ["POL-DELIVERY-3"],
                }
            )
        return response(
            [
                {
                    "id": "msg_eval",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": text, "annotations": []}],
                }
            ]
        )

    item = {"id": "E1", "slice": "exact", "question": "delivery service credit policy"}
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with OpenAI(api_key="local-test-placeholder", http_client=http, max_retries=0) as client:
            report = evaluate(
                client,
                "answer-model",
                {"version": "test", "review_status": "draft", "cases": [item, item]},
                max_calls=4,
                judge_model="judge-model",
                max_judge_calls=1,
                price_card={
                    "version": "synthetic-test-rates",
                    "as_of": "2026-10-20",
                    "source_url": "local-test",
                    "models": {
                        "answer-model": {"input": 2, "cached_input": 1, "output": 4},
                        "judge-model": {"input": 1, "cached_input": 0.5, "output": 2},
                    },
                },
            )
    assert report["actual_model_calls"] == 4 and report["actual_judge_calls"] == 1
    assert len(calls) == 5
    assert report["semantic_accuracy"] is None
    assert report["estimated_token_cost_usd"] == 0.00135
    assert report["outcomes"][0]["model_judge"]["judgment"]["verdict"] == "fail"
    assert report["outcomes"][1]["model_judge"]["status"] == "not-run"
    assert report["slice_results"]["exact"]["total"] == 2


def test_inconsistent_judge_verdict_is_rejected():
    parsed = {
        "claims_supported": False,
        "no_unauthorized_promise": True,
        "useful_next_step": True,
        "rationale": "Unsupported.",
        "verdict": "pass",
    }
    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=lambda **kwargs: SimpleNamespace(
                status="completed", output_parsed=parsed, usage=None
            )
        )
    )
    with pytest.raises(ValueError, match="inconsistent"):
        judge_answer(
            client,
            "judge",
            "question",
            {
                "status": "supported",
                "answer": "claim",
                "citations": [],
                "suggested_credit_naira": None,
            },
            {},
        )


def review_report():
    return {
        "dataset_sha256": "revision-1",
        "evaluation_fingerprint": "specific-generated-run",
        "outcomes": [
            {
                "id": "E1",
                "model_judge": {"status": "judged-uncalibrated", "judgment": {"verdict": "pass"}},
            },
            {"id": "E2", "model_judge": {"status": "not-run"}},
        ],
    }


def labels():
    return {
        "dataset_sha256": "revision-1",
        "evaluation_fingerprint": "specific-generated-run",
        "reviewer": "Test reviewer",
        "reviewed_at": "2026-10-20",
        "cases": {
            "E1": {
                "claims_supported": False,
                "no_unauthorized_promise": True,
                "useful_next_step": True,
            }
        },
    }


def test_human_review_is_partial_revision_bound_and_can_disagree_with_judge():
    report = apply_reviews(review_report(), labels())
    summary = report["human_review_summary"]
    assert summary["reviewed_outcomes"] == 1 and summary["total_outcomes"] == 2
    assert summary["judge_agreement_fraction"] == 0
    assert not summary["release_thresholds_approved"]
    assert report["outcomes"][0]["semantic_review"]["reviewer"] == "Test reviewer"


@pytest.mark.parametrize("problem", ["revision", "anonymous", "string_boolean", "unknown_case"])
def test_invalid_human_labels_cannot_be_recorded(problem):
    data = labels()
    if problem == "revision":
        data["dataset_sha256"] = "other"
    elif problem == "anonymous":
        data["reviewer"] = ""
    elif problem == "string_boolean":
        data["cases"]["E1"]["claims_supported"] = "true"
    else:
        data["cases"]["UNKNOWN"] = data["cases"]["E1"]
    with pytest.raises(ValueError):
        apply_reviews(review_report(), data)


def test_preflight_without_keys_reports_blockers_without_provider_calls(tmp_path, monkeypatch):
    from scripts.contact1_preflight import configuration

    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "RELAY_ALLOW_LIVE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("RELAY_VECTOR_PATH", str(tmp_path / "absent"))
    report = configuration()
    assert not any(report["configured"].values())
    assert report["provider_calls"] == 0 and not report["class_ready"]
    assert not report["index_manifest_present"]
    assert not (tmp_path / "absent").exists()


def test_cost_estimate_uses_explicit_rates_cached_and_embedding_usage():
    from teaching.cost_reference import quote_run

    # Synthetic test rates, not OpenAI prices.
    card = {
        "version": "test-rates",
        "as_of": "2026-10-20",
        "source_url": "local-test",
        "models": {
            "answer": {"input": 2, "cached_input": 1, "output": 4},
            "embedding": {"input": 0.5},
        },
    }
    run = {
        "model": "answer",
        "trace": {
            "model_calls": 2,
            "input_tokens": 100,
            "cached_input_tokens": 20,
            "output_tokens": 10,
            "embedding_calls": 1,
            "embedding_model": "embedding",
            "embedding_input_tokens": 20,
        },
    }
    assert quote_run(run, card)["estimated_usd"] == 0.00023
    run["trace"]["embedding_input_tokens"] = None
    with pytest.raises(ValueError, match="incomplete"):
        quote_run(run, card)
