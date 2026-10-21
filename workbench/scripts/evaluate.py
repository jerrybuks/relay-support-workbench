"""Compare deterministic retrieval fixtures. This is not a live-model quality evaluation."""

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from relay.assistant import investigate, title_retrieval  # noqa: E402
from relay.store import Store  # noqa: E402
from teaching.contact1_reference import search_reference  # noqa: E402


def run():
    dataset = json.loads((ROOT / "evals/cases.json").read_text())
    results = {}
    with tempfile.TemporaryDirectory(prefix="relay-eval-") as temp:
        store = Store(Path(temp) / "evaluation.sqlite")
        token, actor = store.create_session("agent")
        for name, retrieve in [
            ("baseline", title_retrieval),
            ("contact1_lexical_intermediate", search_reference),
        ]:
            outcomes = []
            for item in dataset["cases"]:
                case = store.case(actor, item.get("case", "RY-1042"))
                answer = investigate(store, actor, case, item["question"], retrieve)
                ids = [c["id"] for c in answer["citations"]]
                passed = all(s in ids for s in item.get("sources", []))
                if item.get("abstain"):
                    passed = passed and answer["status"] == "insufficient_evidence"
                passed = passed and not any(s in ids for s in item.get("forbidden", []))
                passed = passed and not any("CANARY" in c["excerpt"] for c in answer["citations"])
                if "credit" in item:
                    passed = passed and answer["suggested_credit_naira"] == item["credit"]
                outcomes.append(
                    {
                        "id": item["id"],
                        "slice": item["slice"],
                        "passed": passed,
                        "status": answer["status"],
                        "source_ids": ids,
                    }
                )
            results[name] = {
                "passed": sum(r["passed"] for r in outcomes),
                "total": len(outcomes),
                "cases": outcomes,
            }
    fingerprint = hashlib.sha256()
    for folder in [ROOT / "src", ROOT / "teaching", ROOT / "evals", ROOT / "scripts"]:
        for path in sorted(folder.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                fingerprint.update(str(path.relative_to(ROOT)).encode() + path.read_bytes())
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": dataset["version"],
        "dataset_review_status": dataset["review_status"],
        "provider": "fixture",
        "model": None,
        "corpus": "synthetic-kora-1",
        "live_api_cost_usd": 0,
        "model_accuracy": None,
        "tokens": None,
        "live_latency_p95": None,
        "source_fingerprint_sha256": fingerprint.hexdigest(),
        "base_git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "scope": "Retrieval presence/abstention, access and deterministic policy checks; "
        "not live generation, embedding quality, semantic entailment or customer acceptance.",
        "results": results,
    }
    target = ROOT / "evidence"
    target.mkdir(exist_ok=True)
    (target / "fixture-evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Relay fixture evaluation",
        "",
        report["scope"],
        "",
        f"Dataset: {dataset['version']} ({dataset['review_status']}).",
        "Provider: fixture; no model call, tokens or live accuracy measured.",
        "",
        "| Profile | Checks passed |",
        "| --- | --- |",
    ]
    lines += [
        f"| {name} | {result['passed']}/{result['total']} |" for name, result in results.items()
    ]
    (target / "fixture-evaluation.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({name: f"{r['passed']}/{r['total']}" for name, r in results.items()}))
    reference = results["contact1_lexical_intermediate"]
    return 0 if reference["passed"] == reference["total"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
