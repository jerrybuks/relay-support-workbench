"""Safe deterministic M0 provider. No OpenAI call or embedding is implied."""

import re
import time
import uuid


def title_retrieval(documents, question):
    """Intentionally limited baseline: title words only; a Contact 1 improvement target."""
    words = set(re.findall(r"[a-z]+", question.lower())) - {
        "the",
        "a",
        "is",
        "for",
        "can",
        "what",
        "my",
        "we",
        "to",
        "of",
        "and",
        "in",
        "i",
    }
    ranked = [(len(words & set(re.findall(r"[a-z]+", d["title"].lower()))), d) for d in documents]
    return [
        d for score, d in sorted(ranked, key=lambda pair: (-pair[0], pair[1]["id"])) if score >= 2
    ][:2]


def credit_limit(case):
    shipment = case["shipment"]
    if shipment["service"] != "Express" or not shipment["delivered"]:
        return 0
    if shipment["delay_hours"] <= 24:
        return 0
    return min(shipment["fee_naira"] // 4, 5000)


def investigate(store, actor, case, question, retrieve=title_retrieval):
    started = time.perf_counter()
    # The same permissioned source list is supplied to all retrieval implementations.
    documents = store.documents(actor)
    retrieved = retrieve(documents, question)
    allowed = {d["id"]: d for d in documents}
    # Enforce IDs and canonical contents after retrieval, even for an untrusted adapter.
    evidence = [allowed[d["id"]] for d in retrieved if d.get("id") in allowed]
    shipment = case["shipment"]
    limit = credit_limit(case)
    answer = {
        "id": uuid.uuid4().hex,
        "provider": "fixture",
        "model": None,
        "status": "supported" if evidence else "insufficient_evidence",
        "answer": "I could not find enough published policy evidence for that wording. "
        "Try a policy title, or review the knowledge library. Do not promise a resolution yet.",
        "citations": [
            {"id": d["id"], "title": d["title"], "version": d["version"], "excerpt": d["text"]}
            for d in evidence
        ],
        "tools": [
            {
                "name": "get_shipment",
                "status": "completed",
                "arguments": {"shipment_id": shipment["id"]},
                "result": {"status": shipment["status"], "delay_hours": shipment["delay_hours"]},
            },
            {
                "name": "search_policies",
                "status": "completed",
                "result": {"source_ids": [d["id"] for d in evidence]},
            },
        ],
        "suggested_credit_naira": None,
        "trace": {
            "retrieval": retrieve.__name__,
            "source_count": len(evidence),
            "input_tokens": None,
            "output_tokens": None,
            "api_cost_usd": 0,
            "prompt_version": "fixture-1",
            "corpus_version": "synthetic-kora-1",
        },
    }
    if evidence:
        answer["answer"] = "\n\n".join(d["text"] for d in evidence)
        if any(d["id"] == "POL-DELIVERY-3" for d in evidence):
            answer["answer"] += f"\n\nShipment check: {shipment['status']}. " + (
                f"The maximum eligible service credit is ₦{limit:,}. "
                "You can submit a proposal for supervisor review."
                if limit
                else "This shipment does not meet the delay-credit conditions."
            )
            answer["suggested_credit_naira"] = limit or None
    answer["trace"]["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return answer
