"""Actual LangGraph execution of the same permissioned investigation stages."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class RunState(TypedDict):
    ready: bool


def execute_graph(prepare, retrieve, generate, validate, has_evidence):
    def preparation(state):
        prepare()
        return {"ready": False}

    def retrieval(state):
        retrieve()
        return {"ready": has_evidence()}

    def generation(state):
        generate()
        return {}

    def validation(state):
        validate()
        return {}

    graph = StateGraph(RunState)
    for name, callback in (
        ("prepare", preparation),
        ("retrieve", retrieval),
        ("generate", generation),
        ("validate", validation),
    ):
        graph.add_node(name, callback)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "retrieve")
    graph.add_conditional_edges(
        "retrieve", lambda state: "generate" if state["ready"] else "validate"
    )
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", END)
    return graph.compile().invoke({"ready": False}, config={"recursion_limit": 8})
