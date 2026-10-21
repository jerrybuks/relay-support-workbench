"""Two explicitly selected models on one frozen dataset/corpus; exploratory, not a release grade."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_live import evaluate  # noqa: E402
from teaching.cost_reference import load_price_card  # noqa: E402
from teaching.provider_connection import provider_name  # noqa: E402
from teaching.rag_reference import VectorRag  # noqa: E402
from teaching.responses_reference import live_client  # noqa: E402


def compare(
    client,
    models,
    dataset,
    rag,
    *,
    max_calls=24,
    max_embeddings=12,
    price_card=None,
    evaluator=evaluate,
):
    if len(models) != 2 or len(set(models)) != 2 or not dataset["cases"]:
        raise ValueError("Choose exactly two distinct models and a nonempty dataset")
    cases = len(dataset["cases"])
    if max_calls < cases * 4 or max_embeddings < cases * 2:
        raise ValueError("Budget must reserve both complete fixed-workflow experiments")
    revision = rag.manifest()["revision"]
    reports = []
    for model in models:
        if rag.manifest()["revision"] != revision:
            raise ValueError("Corpus changed during comparison")
        reports.append(
            evaluator(
                client,
                model,
                dataset,
                cases * 2,
                rag=rag,
                max_embedding_calls=cases,
                price_card=price_card,
            )
        )
    if rag.manifest()["revision"] != revision:
        raise ValueError("Corpus changed during comparison")
    complete = all(r["completed_cases"] == cases for r in reports)
    return {
        "provider": provider_name(client),
        "experiment": "two-model fixed-workflow comparison",
        "complete": complete,
        "all_contract_checks_passed": all(r["contract_checks_passed"] == cases for r in reports),
        "corpus_revision": revision,
        "dataset_sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True).encode()).hexdigest(),
        "actual_model_calls": sum(r["actual_model_calls"] for r in reports),
        "actual_embedding_calls": sum(r["actual_embedding_calls"] for r in reports),
        "statistical_limit": (
            f"Exploratory: {cases} draft cases per model, one pass; "
            "no stable speed/semantic-quality conclusion."
        ),
        "human_review": "required",
        "summary": [
            {
                k: r[k]
                for k in (
                    "model",
                    "completed_cases",
                    "total_cases",
                    "contract_checks_passed",
                    "semantic_accuracy",
                    "model_run_latency_p95_ms",
                    "input_tokens",
                    "output_tokens",
                    "estimated_token_cost_usd",
                )
            }
            for r in reports
        ],
        "reports": reports,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alternate-model",
        required=True,
        help="Comparison only; does not change the configured primary model",
    )
    parser.add_argument("--dataset", type=Path, default=ROOT / "evals/contact1-comparison.json")
    parser.add_argument("--price-card", type=Path)
    parser.add_argument("--max-model-calls", type=int, default=24)
    parser.add_argument("--max-embedding-calls", type=int, default=12)
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".runtime/c1-preparation/model-comparison.json"
    )
    args = parser.parse_args()
    client, model = live_client()
    rag = None
    try:
        rag = VectorRag(client)
        report = compare(
            client,
            [model, args.alternate_model],
            json.loads(args.dataset.read_text()),
            rag,
            max_calls=args.max_model_calls,
            max_embeddings=args.max_embedding_calls,
            price_card=load_price_card(args.price_card) if args.price_card else None,
        )
    except Exception as exc:
        report = {
            "complete": False,
            "status": "unavailable",
            "exception_type": type(exc).__name__,
            "http_status": getattr(exc, "status_code", None),
        }
    finally:
        if rag:
            rag.close()
        client.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "reports"}, indent=2))
    return 0 if report.get("complete") and report.get("all_contract_checks_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
