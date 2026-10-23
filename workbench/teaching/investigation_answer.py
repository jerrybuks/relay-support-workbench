"""Build grounded model input, run read-only tools and validate the final citations."""

import json

from relay.assistant import credit_limit

from .agent_harness import InvestigationFailure, read_tools
from .observability_reference import stage
from .responses_reference import GroundedAnswer


def generate_answer(
    invoke, question, case, evidence, history_context, tools, execution_mode, instructions
):
    passages = [
        {
            "id": d.get("chunk_id", d["id"]),
            "source_id": d["id"],
            "title": d["title"],
            "version": d["version"],
            "excerpt": d["excerpt"],
        }
        for d in evidence
    ]
    history = [
        {"role": "developer", "content": instructions},
        *history_context,
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": question,
                    "evidence": passages,
                    "shipment_id": case["shipment"]["id"],
                }
            ),
        },
    ]
    with stage("tool_workflow" if execution_mode == "workflow" else "agent_loop", "agent"):
        read_tools(invoke, history, case, evidence, tools, execution_mode)
    return invoke("answer_generation", structured=True, input=history)


def validate_answer(final, evidence, case, run):
    if not evidence:
        return
    with stage("output_validation", "guardrail"):
        if final.output_parsed is None:
            raise InvestigationFailure("refusal_or_missing_output")
        parsed = GroundedAnswer.model_validate(final.output_parsed)
        allowed = {d.get("chunk_id", d["id"]): d for d in evidence}
        if any(s not in allowed for s in parsed.cited_ids):
            raise InvestigationFailure("citation_scope")
        if bool(parsed.cited_ids) != (parsed.status == "supported"):
            raise InvestigationFailure("citation_status")
        if not parsed.answer.strip():
            raise InvestigationFailure("empty_answer")
        run.update(
            status=parsed.status,
            answer=parsed.answer,
            citations=[allowed[s] for s in dict.fromkeys(parsed.cited_ids)],
        )
        if parsed.status == "supported" and any(
            c["id"] == "POL-DELIVERY-3" for c in run["citations"]
        ):
            run["suggested_credit_naira"] = credit_limit(case) or None
