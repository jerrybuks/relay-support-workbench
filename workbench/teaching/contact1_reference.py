"""Contact 1 lexical retrieval reference. No embeddings or live model implied."""

import re
import sqlite3

from relay.main import create_app as baseline

STOP = {
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
    "any",
    "it",
    "how",
    "do",
    "does",
    "this",
    "please",
    "about",
    "with",
    "you",
    "me",
}


def search_reference(documents, question):
    terms = sorted(set(re.findall(r"[a-z]+", question.lower())) - STOP)
    if not terms:
        return []
    # The index is ephemeral and contains only the caller-authorized corpus.
    # No global search followed by post-hoc tenant filtering.
    with sqlite3.connect(":memory:") as index:
        index.execute("CREATE VIRTUAL TABLE passages USING fts5(id UNINDEXED,title,tags,text)")
        index.executemany(
            "INSERT INTO passages VALUES (?,?,?,?)",
            [(d["id"], d["title"], d.get("tags", ""), d["text"]) for d in documents],
        )
        query = " OR ".join('"' + term + '"' for term in terms)
        rows = index.execute(
            "SELECT id FROM passages WHERE passages MATCH ? "
            "ORDER BY bm25(passages,0,3,2,1) LIMIT 2",
            (query,),
        ).fetchall()
    allowed = {d["id"]: d for d in documents}
    results = []
    for row in rows:
        document = allowed[row[0]]
        vocabulary = set(
            re.findall(
                r"[a-z]+",
                " ".join([document["title"], document.get("tags", ""), document["text"]]).lower(),
            )
        )
        # A lone generic hit (e.g. "supervisor") is not enough evidence for an answer.
        # This threshold is a small fixture heuristic, not calibrated semantic relevance.
        if len(set(terms) & vocabulary) >= 2:
            results.append(document)
    return results


def create_app():
    import os
    from pathlib import Path

    path = os.getenv("RELAY_REFERENCE_DB", str(Path(__file__).parents[1] / ".runtime/c1.sqlite"))
    return baseline(
        path,
        retriever=search_reference,
        checkpoint="contact-1-lexical-reference",
        session_cookie="relay_c1_retrieval",
    )
