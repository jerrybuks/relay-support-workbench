"""Small actual LangChain/LangGraph component comparison; no model call."""

from typing import TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph


class ReviewState(TypedDict):
    text: str
    chunks: list[str]
    state: str


def build_review_graph():
    splitter = RecursiveCharacterTextSplitter(chunk_size=180, chunk_overlap=25)

    def chunk(state):
        return {"chunks": splitter.split_text(state["text"]), "state": "candidate"}

    def queue(state):
        return {"state": "awaiting_human_review" if state["chunks"] else "rejected_empty"}

    graph = StateGraph(ReviewState)
    graph.add_node("chunk", chunk)
    graph.add_node("queue", queue)
    graph.add_edge(START, "chunk")
    graph.add_edge("chunk", "queue")
    graph.add_edge("queue", END)
    return graph.compile()
