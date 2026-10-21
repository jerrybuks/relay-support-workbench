"""Read-only tool dispatch shared by workflow and bounded agent-loop demonstrations."""

import json
from typing import Literal

from relay.models import Ask

from .observability_reference import stage
from .tool_loop_reference import TOOLS


class LiveAsk(Ask):
    # Explicit opt-in: saving an exchange and sending prior exchanges are distinct choices.
    memory_mode: Literal["stateless", "case"] = "stateless"
    execution_mode: Literal["workflow", "agent"] = "workflow"
    runtime: Literal["direct", "langgraph"] = "direct"
    stream: bool = False


class InvestigationFailure(ValueError):
    """Fixed codes only; never exception messages from a provider."""


POLICY_TOOL = {
    "type": "function",
    "name": "read_policy_chunk",
    "strict": True,
    "description": "Inspect a chunk already present in this run's authorized evidence.",
    "parameters": {
        "type": "object",
        "properties": {"chunk_id": {"type": "string"}},
        "required": ["chunk_id"],
        "additionalProperties": False,
    },
}


def execute_tools(response, history, case, evidence, tools, budget):
    calls = [item for item in response.output if item.type == "function_call"]
    if len(calls) > min(2, budget):
        raise InvestigationFailure("tool_budget")
    allowed = {d.get("chunk_id", d["id"]): d for d in evidence}
    # Validate the WHOLE batch before executing any call.
    pending = []
    for call in calls:
        args = json.loads(call.arguments)
        if not isinstance(args, dict):
            raise InvestigationFailure("tool_scope")
        if call.name == "get_shipment" and args == {"shipment_id": case["shipment"]["id"]}:
            result = case["shipment"]
        elif (
            call.name == "read_policy_chunk"
            and set(args) == {"chunk_id"}
            and args["chunk_id"] in allowed
        ):
            source = allowed[args["chunk_id"]]
            result = {k: source[k] for k in ("id", "version", "excerpt")}
        else:
            raise InvestigationFailure("tool_scope")
        pending.append((call, args, result))
    history.extend(response.output)  # Preserve reasoning items within this run only.
    for call, args, result in pending:
        with stage(call.name, "tool"):
            tools.append(
                {
                    "name": call.name,
                    "status": "completed",
                    "arguments": args,
                    "result": {"shipment_id": result.get("id")}
                    if call.name == "get_shipment"
                    else {"source_id": result["id"]},
                }
            )
            history.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result),
                }
            )
    return len(calls)


def read_tools(invoke, history, case, evidence, tools, mode):
    response = invoke(
        "tool_selection",
        input=history,
        tools=TOOLS,
        tool_choice={"type": "function", "name": "get_shipment"},
        parallel_tool_calls=False,
    )
    if len([item for item in response.output if item.type == "function_call"]) != 1:
        raise InvestigationFailure("tool_budget")
    if (
        next(item for item in response.output if item.type == "function_call").name
        != "get_shipment"
    ):
        raise InvestigationFailure("tool_scope")
    execute_tools(response, history, case, evidence, tools, 1)
    if mode == "workflow":
        return
    remaining = 3
    for _ in range(2):
        response = invoke(
            "agent_planning",
            input=history,
            tools=TOOLS + [POLICY_TOOL],
            tool_choice="auto",
            parallel_tool_calls=False,
        )
        count = execute_tools(response, history, case, evidence, tools, remaining)
        if not count:
            return
        remaining -= count
        if remaining == 0:
            break
    raise InvestigationFailure("agent_turn_budget")
