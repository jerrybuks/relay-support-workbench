"""Merge explicit human labels into a local evaluation report; no provider calls."""

import argparse
import json
from datetime import date
from pathlib import Path

CHECKS = ("claims_supported", "no_unauthorized_promise", "useful_next_step")


def apply_reviews(report, reviews):
    if not reviews.get("reviewer", "").strip() or not reviews.get("reviewed_at", "").strip():
        raise ValueError("A named reviewer and review date are required")
    date.fromisoformat(reviews["reviewed_at"])
    if reviews.get("evaluation_fingerprint") != report.get(
        "evaluation_fingerprint"
    ) or not report.get("evaluation_fingerprint"):
        raise ValueError("Human labels belong to a different generated evaluation")
    if reviews.get("dataset_sha256") != report["dataset_sha256"]:
        raise ValueError("Human labels belong to a different dataset revision")
    items = reviews.get("cases", {})
    ids = {o.get("evaluation_id", o["id"]) for o in report["outcomes"]}
    if set(items) - ids:
        raise ValueError("Human labels include cases absent from this report")
    for label in items.values():
        if not isinstance(label, dict) or any(type(label.get(k)) is not bool for k in CHECKS):
            raise ValueError("Every labeled case needs three explicit boolean rubric checks")
    agreements = []
    reviewed = []
    for outcome in report["outcomes"]:
        key = outcome.get("evaluation_id", outcome["id"])
        if key not in items:
            continue
        label = items[key]
        outcome["semantic_review"] = {
            "status": "human-reviewed",
            "reviewer": reviews["reviewer"],
            "reviewed_at": reviews["reviewed_at"],
            **{k: label[k] for k in CHECKS},
        }
        passed = all(label[k] for k in CHECKS)
        reviewed.append(passed)
        judge = outcome.get("model_judge", {})
        if judge.get("status") == "judged-uncalibrated":
            agreements.append((judge["judgment"]["verdict"] == "pass") == passed)
    report["human_review_summary"] = {
        "reviewer": reviews["reviewer"],
        "reviewed_outcomes": len(reviewed),
        "total_outcomes": len(report["outcomes"]),
        "passed": sum(reviewed),
        "pass_fraction": sum(reviewed) / len(reviewed) if reviewed else None,
        "judge_compared_outcomes": len(agreements),
        "judge_agreement_fraction": sum(agreements) / len(agreements) if agreements else None,
        "release_thresholds_approved": False,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = apply_reviews(
        json.loads(args.report.read_text()), json.loads(args.reviews.read_text())
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["human_review_summary"]))


if __name__ == "__main__":
    main()
