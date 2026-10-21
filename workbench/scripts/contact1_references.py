"""Generate/check slide code locations from Python symbols, without importing references."""

import argparse
import ast
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "src/relay/static/contact1.html"
REFERENCES = {
    "harness": [
        ("teaching/investigation_reference.py", "make_investigator"),
        ("teaching/agent_harness.py", "read_tools"),
    ],
    "governance": [("src/relay/service.py", "decide")],
    "request-path": [("src/relay/main.py", "create_app.run_query")],
    "responses": [
        ("teaching/investigation_reference.py", "make_investigator.investigate.invoke"),
        ("teaching/responses_reference.py", "GroundedAnswer"),
    ],
    "rag": [
        ("teaching/rag_reference.py", "VectorRag._embed_request"),
        ("teaching/rag_reference.py", "VectorRag.search"),
    ],
    "evidence": [
        ("teaching/investigation_reference.py", "retrieve_evidence"),
        ("teaching/investigation_reference.py", "make_investigator.investigate.validate_stage"),
    ],
    "tools": [
        ("teaching/agent_harness.py", "execute_tools"),
        ("teaching/agent_harness.py", "read_tools"),
    ],
    "memory": [("teaching/memory_reference.py", "conversation_context")],
    "guardrails": [
        ("teaching/agent_harness.py", "execute_tools"),
        ("src/relay/service.py", "propose"),
    ],
    "streaming": [
        ("teaching/streaming_reference.py", "install_streaming"),
        ("teaching/investigation_reference.py", "make_investigator.investigate.invoke"),
    ],
    "tracing": [("teaching/observability_reference.py", "RunObservation.stage")],
    "evaluation": [
        ("scripts/evaluate_live.py", "evaluate"),
        ("teaching/semantic_evaluation.py", "judge_answer"),
    ],
    "choices": [
        ("teaching/runtime_graph.py", "execute_graph"),
        ("teaching/provider_settings.py", "provider_options"),
    ],
    "demo-baseline": [("teaching/rag_reference.py", "VectorRag.search")],
    "demo-rag": [
        ("teaching/rag_reference.py", "VectorRag.search"),
        ("teaching/investigation_reference.py", "make_investigator.investigate.invoke"),
    ],
    "demo-boundaries": [
        ("teaching/memory_reference.py", "conversation_context"),
        ("src/relay/main.py", "create_app.forget"),
    ],
    "demo-evaluate": [("scripts/evaluate_live.py", "evaluate")],
    "demo-codex": [
        ("src/relay/main.py", "create_app.run_query"),
        ("src/relay/service.py", "decide"),
    ],
    "setup": [("scripts/contact1_preflight.py", "configuration")],
    "indexing": [
        ("teaching/rag_reference.py", "native_chunks"),
        ("teaching/rag_reference.py", "VectorRag.build"),
    ],
    "openai-state": [("teaching/openai_state_reference.py", "compare_state")],
    "stream-events": [("teaching/streaming_reference.py", "install_streaming")],
    "runtime-details": [
        ("teaching/runtime_graph.py", "execute_graph"),
        ("teaching/agent_harness.py", "read_tools"),
    ],
    "privacy": [
        ("teaching/observability_reference.py", "safe_metadata"),
        ("teaching/provider_connection.py", "connect"),
    ],
    "eval-commands": [
        ("scripts/evaluate_live.py", "main"),
        ("teaching/cost_reference.py", "quote_run"),
    ],
    "human-review": [("scripts/review_evaluation.py", "apply_reviews")],
}


def location(path, symbol):
    tree = ast.parse((ROOT / path).read_text())
    for name in symbol.split("."):
        tree = next(
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        )
    return f"workbench/{path}:{tree.lineno}"


def process_deck(deck, required, *, write=False):
    source = deck.read_text()
    checked = []

    def section(match):
        body = match.group()
        sid = re.search(r'\bid="([^"]+)"', body).group(1)
        expected = [location(path, symbol) for path, symbol in REFERENCES.get(sid, [])]
        actual = re.findall(r'data-code-location="([^"]+)"', body)
        if not write:
            if actual != expected:
                raise SystemExit(
                    f"Stale code references on {sid}; "
                    "run contact1_references.py --write and format the deck."
                )
        elif expected:
            body = re.sub(r'<div class="code-footnote".*?</div>\s*', "", body, flags=re.S)
            buttons = [
                f'<button type="button" data-code-location="{html.escape(loc)}" '
                f'title="Copy location for {html.escape(symbol)}">'
                f"{html.escape(loc)}</button>"
                for loc, (_, symbol) in zip(expected, REFERENCES[sid], strict=True)
            ]
            footnote = (
                '<div class="code-footnote" aria-label="Code references">'
                "<span>Code · click to copy</span>" + "".join(buttons) + "</div>\n"
            )
            body = body.replace(
                '<aside class="speaker-notes" hidden>',
                footnote + '<aside class="speaker-notes" hidden>',
                1,
            )
        if expected:
            checked.append(sid)
        return body

    result = re.sub(r"<section\b[^>]*>.*?</section>", section, source, flags=re.S)
    if set(checked) != required:
        raise SystemExit("A referenced slide is missing")
    if write:
        deck.write_text(result)
    print(
        f"{deck.name}: slide code references {'updated' if write else 'verified'}: "
        f"{len(checked)} slides"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    concept_ids = {
        "why",
        "outcomes",
        "harness",
        "governance",
        "request-path",
        "responses",
        "rag",
        "evidence",
        "tools",
        "memory",
        "guardrails",
        "streaming",
        "tracing",
        "evaluation",
        "choices",
    }
    process_deck(DECK, set(REFERENCES), write=args.write)
    process_deck(
        DECK.with_name("contact1-concepts.html"), concept_ids & set(REFERENCES), write=args.write
    )


if __name__ == "__main__":
    main()
