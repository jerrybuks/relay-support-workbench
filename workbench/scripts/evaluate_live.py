"""Opt-in billable C1 evaluation; contract scores plus a human semantic-review worksheet.

Uses the same synthetic dataset as fixture evaluation, never the owner's database.
Generated text remains in an ignored local report until reviewed for sharing.
"""

import argparse
import hashlib
import json
import math
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openai import OpenAIError  # noqa: E402

from relay.store import Store  # noqa: E402
from teaching.contact1_live import PROMPT_VERSION, make_investigator  # noqa: E402
from teaching.cost_reference import load_price_card, quote_run  # noqa: E402
from teaching.provider_connection import provider_name  # noqa: E402
from teaching.rag_reference import VectorRag  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402
from teaching.semantic_evaluation import judge_answer  # noqa: E402


def evaluate(
    client,
    model,
    dataset,
    max_calls,
    rag=None,
    max_embedding_calls=20,
    judge_model=None,
    max_judge_calls=0,
    repetitions=1,
    price_card=None,
    execution_mode="workflow",
    runtime="direct",
):
    outcomes = []
    calls = 0
    judge_calls = 0
    with tempfile.TemporaryDirectory(prefix="relay-live-eval-") as temp:
        store = Store(Path(temp) / "evaluation.sqlite")
        _, actor = store.create_session("agent")
        investigate = make_investigator(client, model, rag=rag)
        initial_embeddings = rag.embedding_calls if rag else 0
        for item in dataset["cases"] * repetitions:
            # Reserve the complete request budget before starting another case.
            reservation = 2 if execution_mode == "workflow" else 4
            if calls + reservation > max_calls or (
                rag and rag.embedding_calls - initial_embeddings >= max_embedding_calls
            ):
                break
            case = store.case(actor, item.get("case", "RY-1042"))
            run = investigate(
                store, actor, case, item["question"], execution_mode=execution_mode, runtime=runtime
            )
            calls += run["trace"]["model_calls"]
            ids = [c["id"] for c in run["citations"]]
            checks = {
                "available": run["status"] != "unavailable",
                "read_tools_only": all(
                    tool["name"] in {"search_policies", "get_shipment", "read_policy_chunk"}
                    for tool in run["tools"]
                ),
                "within_request_budget": run["trace"]["model_calls"] <= reservation,
                "expected_sources": all(s in ids for s in item.get("sources", [])),
                "forbidden_sources": not any(s in ids for s in item.get("forbidden", [])),
                "canary_absent": not any("CANARY" in c["excerpt"] for c in run["citations"]),
                "expected_abstention": not item.get("abstain")
                or run["status"] == "insufficient_evidence",
                "server_credit": "credit" not in item
                or run["suggested_credit_naira"] == item["credit"],
            }
            retrieved = list(
                dict.fromkeys(h["id"] for h in run["trace"].get("retrieved_chunks", []))
            )
            expected = set(item.get("sources", []))
            recall = len(expected.intersection(retrieved)) / len(expected) if expected else None
            reciprocal_rank = (
                next(
                    (1 / (rank + 1) for rank, source in enumerate(retrieved) if source in expected),
                    0,
                )
                if expected
                else None
            )
            judgment = {"status": "not-run", "human_calibrated": False}
            if judge_model and judge_calls < max_judge_calls and run["status"] != "unavailable":
                judge_calls += 1
                try:
                    judgment = judge_answer(
                        client, judge_model, item["question"], run, case["shipment"]
                    )
                except (OpenAIError, ValueError):
                    judgment = {"status": "unavailable", "human_calibrated": False}
            outcomes.append(
                {
                    "id": item["id"],
                    "evaluation_id": run["id"],
                    "slice": item["slice"],
                    "question": item["question"],
                    "checks": checks,
                    "passed": all(checks.values()),
                    "run": run,
                    "model_judge": judgment,
                    "retrieval_metrics": {
                        "source_recall_at_k": recall,
                        "reciprocal_rank": reciprocal_rank,
                    },
                    "semantic_review": {
                        "status": "pending-human-review",
                        "reviewer": None,
                        "claims_supported": None,
                        "no_unauthorized_promise": None,
                        "useful_next_step": None,
                        "notes": None,
                    },
                }
            )
    durations = sorted(
        o["run"]["trace"]["duration_ms"] for o in outcomes if o["run"]["trace"]["model_calls"]
    )
    measured = [o["run"]["trace"] for o in outcomes if o["run"]["trace"]["model_calls"]]
    usage_complete = bool(measured) and all(t["input_tokens"] is not None for t in measured)
    cost_quotes = []
    cost_complete = price_card is not None
    for outcome in outcomes:
        if price_card is not None:
            try:
                quote = quote_run(outcome["run"], price_card)
                judge = outcome["model_judge"]
                if judge.get("status") == "judged-uncalibrated":
                    judge_quote = quote_run(
                        {
                            "model": judge["model"],
                            "trace": {
                                "model_calls": 1,
                                "input_tokens": judge["input_tokens"],
                                "output_tokens": judge["output_tokens"],
                                "cached_input_tokens": judge.get("cached_input_tokens", 0),
                            },
                        },
                        price_card,
                    )
                    quote["estimated_usd"] += judge_quote["estimated_usd"]
                elif judge.get("status") == "unavailable":
                    raise ValueError("judge_usage_incomplete")
                outcome["cost_quote"] = quote
                cost_quotes.append(quote["estimated_usd"])
            except (KeyError, ValueError, TypeError):
                cost_complete = False
    relevant = [
        o["retrieval_metrics"]
        for o in outcomes
        if o["retrieval_metrics"]["source_recall_at_k"] is not None
    ]
    return {
        "retrieval_metrics": {
            "mean_source_recall_at_k": sum(m["source_recall_at_k"] for m in relevant)
            / len(relevant)
            if rag and relevant
            else None,
            "mean_reciprocal_rank": sum(m["reciprocal_rank"] for m in relevant) / len(relevant)
            if rag and relevant
            else None,
            "threshold_calibrated": False,
        },
        "evaluation_fingerprint": hashlib.sha256(
            json.dumps(
                [
                    {
                        "evaluation_id": o["evaluation_id"],
                        "question": o["question"],
                        "run": o["run"],
                    }
                    for o in outcomes
                ],
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        "created_at": datetime.now(UTC).isoformat(),
        "provider": provider_name(client),
        "model": model,
        "dataset": dataset["version"],
        "dataset_review_status": dataset["review_status"],
        "dataset_sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True).encode()).hexdigest(),
        "prompt_version": PROMPT_VERSION,
        "corpus": "synthetic-kora-1",
        "scope": "Source/abstention/server-policy contract checks; "
        "semantic accuracy pending human review.",
        "max_model_calls": max_calls,
        "execution_mode": execution_mode,
        "runtime": runtime,
        "max_judge_calls": max_judge_calls,
        "actual_judge_calls": judge_calls,
        "judge_model": judge_model,
        "repetitions": repetitions,
        "slice_results": {
            name: {
                "total": sum(o["slice"] == name for o in outcomes),
                "contract_passed": sum(o["slice"] == name and o["passed"] for o in outcomes),
            }
            for name in sorted({o["slice"] for o in outcomes})
        },
        "retrieval": rag.config.mode if rag else "lexical-contract-test",
        "embedding_model": rag.config.model if rag else None,
        "max_embedding_calls": max_embedding_calls,
        "actual_embedding_calls": rag.embedding_calls - initial_embeddings if rag else 0,
        "embedding_input_tokens": sum(
            o["run"]["trace"].get("embedding_input_tokens") or 0 for o in outcomes
        )
        if rag and rag.usage_complete
        else None,
        "actual_model_calls": calls,
        "completed_cases": len(outcomes),
        "total_cases": len(dataset["cases"]) * repetitions,
        "contract_checks_passed": sum(o["passed"] for o in outcomes),
        "semantic_accuracy": None,
        "api_cost_usd": None,
        "estimated_token_cost_usd": round(sum(cost_quotes), 10) if cost_complete else None,
        "cost_basis": {"version": price_card["version"], "as_of": price_card["as_of"]}
        if price_card
        else None,
        "input_tokens": sum(t["input_tokens"] for t in measured) if usage_complete else None,
        "output_tokens": sum(t["output_tokens"] for t in measured) if usage_complete else None,
        "latency_scope": "end-to-end investigation including retrieval; tests use mock transport",
        "model_run_latency_p95_ms": durations[math.ceil(0.95 * len(durations)) - 1]
        if durations
        else None,
        "outcomes": outcomes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-model-calls", type=int, default=40, choices=range(2, 161), metavar="2..160"
    )
    parser.add_argument(
        "--price-card", type=Path, help="Explicit dated JSON rates; no assumed pricing"
    )
    parser.add_argument("--execution-mode", choices=["workflow", "agent"], default="workflow")
    parser.add_argument("--runtime", choices=["direct", "langgraph"], default="direct")
    parser.add_argument("--judge-model", help="Explicit extra billable model; no default judge")
    parser.add_argument("--max-judge-calls", type=int, default=0, choices=range(0, 41))
    parser.add_argument("--repetitions", type=int, default=1, choices=range(1, 4))
    parser.add_argument("--dataset", type=Path, default=ROOT / "evals/cases.json")
    parser.add_argument("--max-embedding-calls", type=int, default=20, choices=range(1, 41))
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/c1-live-evaluation.json")
    args = parser.parse_args()
    if bool(args.judge_model) != bool(args.max_judge_calls):
        parser.error("Provide --judge-model and a nonzero --max-judge-calls together.")
    price_card = load_price_card(args.price_card) if args.price_card else None
    client, model = live_client()
    dataset = json.loads(args.dataset.read_text())
    rag = VectorRag(client)
    try:
        rag.manifest()  # Refuse to spend on generation when the prepared index is missing.
        report = evaluate(
            client,
            model,
            dataset,
            args.max_model_calls,
            rag,
            args.max_embedding_calls,
            args.judge_model,
            args.max_judge_calls,
            args.repetitions,
            price_card,
            args.execution_mode,
            args.runtime,
        )
    finally:
        rag.close()
        client.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "provider",
                    "model",
                    "actual_model_calls",
                    "completed_cases",
                    "total_cases",
                    "contract_checks_passed",
                    "semantic_accuracy",
                ]
            }
        )
    )
    print(f"Review generated claims and evidence locally: {args.output}")
    return 0 if report["contract_checks_passed"] == report["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
