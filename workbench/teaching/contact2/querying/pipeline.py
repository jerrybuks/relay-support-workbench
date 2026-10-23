"""Start here: retrieve passages → generate an answer → validate its citations."""

import time
from typing import Any, Literal

from pydantic import BaseModel

from relay.models import Citation

from .answer import generate_answer, validate_answer
from .retrieval import retrieve_passages


class PolicyAnswer(BaseModel):
    status: Literal["supported", "insufficient_evidence"]
    answer: str
    retrieved_passages: list[Citation]
    citations: list[Citation]
    trace: dict[str, Any]


def answer_question(store, index, client, model, actor, question):
    started = time.perf_counter()

    # 1. Retrieve permitted passages using the question.
    passages, trace = retrieve_passages(index, store.documents(actor), question, actor)
    trace.update(model=model, model_calls=0)
    result = {
        "status": "insufficient_evidence",
        "answer": "No supporting policy passages were found. Try a more specific question.",
        "citations": [],
    }
    if passages:
        # 2. Generate one answer directly from those passages.
        response = generate_answer(client, model, question, passages)
        # 3. Validate the answer and its source references.
        result = validate_answer(response, passages)
        trace.update(
            model_calls=1,
            input_tokens=response.usage.input_tokens if response.usage else None,
            output_tokens=response.usage.output_tokens if response.usage else None,
        )
    trace["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    with store.transaction() as db:
        store.audit(
            db,
            actor,
            "policy.queried",
            {
                "source_ids": list(dict.fromkeys(p["id"] for p in passages)),
                "model_calls": trace["model_calls"],
            },
        )
    return {**result, "retrieved_passages": passages, "trace": trace}
