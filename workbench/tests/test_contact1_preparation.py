"""Preparation contract checks; synthetic control data, no provider calls or collector receipt."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from scripts.contact1_collector import check_collector
from scripts.contact1_compare import compare
from teaching.observability_reference import collector_received


def test_collector_flush_is_not_receipt_and_metadata_has_no_model_payload():
    metadata = []

    class Collector:
        def __init__(self):
            self.api = SimpleNamespace(observations=SimpleNamespace(get_many=self.get))

        def auth_check(self):
            return True

        @contextmanager
        def start_as_current_observation(self, **kwargs):
            metadata.append(kwargs)
            yield SimpleNamespace(update=lambda **data: metadata.append(data))

        def flush(self):
            pass

        def get(self, **kwargs):
            raise LookupError("not available")

    report = check_collector(Collector(), attempts=1)
    assert report["authenticated"] and report["receipt"] == "not-confirmed"
    assert report["openai_calls"] == 0 and not report["live_investigation_verified"]
    assert all("input" not in data for data in metadata)


def test_comparison_reserves_budget_and_freezes_inputs_before_evaluation():
    rag = SimpleNamespace(manifest=lambda: {"revision": "fixed"})
    dataset = {"cases": [{"id": "a"}]}

    def unexpected(*args, **kwargs):
        raise AssertionError("must not start an underfunded experiment")

    with pytest.raises(ValueError, match="Budget"):
        compare(
            None,
            ["primary", "alternate"],
            dataset,
            rag,
            max_calls=2,
            max_embeddings=2,
            evaluator=unexpected,
        )
    seen = []

    def evaluate(client, model, data, budget, **kwargs):
        seen.append((model, data, budget))
        return {
            "model": model,
            "completed_cases": 1,
            "total_cases": 1,
            "contract_checks_passed": 1,
            "semantic_accuracy": None,
            "model_run_latency_p95_ms": 1,
            "input_tokens": 10,
            "output_tokens": 2,
            "estimated_token_cost_usd": None,
            "actual_model_calls": 2,
            "actual_embedding_calls": 1,
        }

    report = compare(
        None,
        ["primary", "alternate"],
        dataset,
        rag,
        max_calls=4,
        max_embeddings=2,
        evaluator=evaluate,
    )
    assert report["complete"] and report["human_review"] == "required"
    assert report["actual_model_calls"] == 4 and report["actual_embedding_calls"] == 2
    assert all(data is dataset and budget == 2 for _, data, budget in seen)
    assert all(row["semantic_accuracy"] is None for row in report["summary"])
    assert report["all_contract_checks_passed"]

    def failed(*args, **kwargs):
        result = evaluate(*args, **kwargs)
        result["contract_checks_passed"] = 0
        return result

    failed_report = compare(
        None,
        ["primary", "alternate"],
        dataset,
        rag,
        max_calls=4,
        max_embeddings=2,
        evaluator=failed,
    )
    assert failed_report["complete"] and not failed_report["all_contract_checks_passed"]
    assert all(row["contract_checks_passed"] == 0 for row in failed_report["summary"])


@pytest.mark.parametrize(
    "trace, parent, root, expected",
    [
        ("wanted", None, True, True),
        ("wanted", "remote-parent", True, True),
        ("different", None, True, False),
        ("wanted", None, False, False),
    ],
)
def test_collector_receipt_requires_matching_root_and_bounded_query(trace, parent, root, expected):
    requests = []

    def get_many(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    trace_id=trace, parent_observation_id=parent, is_root_observation=root
                )
            ]
        )

    client = SimpleNamespace(api=SimpleNamespace(observations=SimpleNamespace(get_many=get_many)))
    assert collector_received(client, "wanted") is expected
    assert requests[0]["limit"] == 1 and requests[0]["is_root_observation"] is True
    assert requests[0]["trace_id"] == "wanted"
    assert "trace_context" in requests[0]["fields"]
    assert requests[0]["to_start_time"] > requests[0]["from_start_time"]
