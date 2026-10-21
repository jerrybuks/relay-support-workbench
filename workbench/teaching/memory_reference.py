"""Caller-managed conversation continuity; saved answers never become policy authority."""

import json

MAX_EXCHANGES = 3
MAX_CHARACTERS = 6000


def conversation_context(store, actor, case_id, documents, mode):
    if mode == "stateless":
        return [], [], {"memory_mode": mode, "memory_exchanges": 0, "memory_characters": 0}
    allowed = {d["id"]: d for d in documents}
    messages, questions = [], []
    used = 0
    skipped = 0
    exchanges = store.messages(actor, case_id)
    selected = []
    for exchange in reversed(exchanges):
        answer = exchange["answer"]
        citations = answer.get("citations", [])
        # Recheck every recalled citation against CURRENT canonical permissions/version/text.
        if (
            answer["status"] != "supported"
            or not citations
            or any(
                c["id"] not in allowed
                or c["version"] != allowed[c["id"]]["version"]
                or c["excerpt"] not in allowed[c["id"]]["text"]
                for c in citations
            )
        ):
            skipped += 1
            continue
        size = len(exchange["question"]) + len(answer["answer"])
        if used + size > MAX_CHARACTERS or len(selected) >= MAX_EXCHANGES:
            break
        used += size
        selected.append(exchange)
    for exchange in reversed(selected):
        messages.extend(
            [
                {"role": "user", "content": exchange["question"]},
                {"role": "assistant", "content": exchange["answer"]["answer"]},
            ]
        )
        questions.append(exchange["question"])
    return (
        messages,
        questions,
        {
            "memory_mode": mode,
            "memory_exchanges": len(selected),
            "memory_characters": used,
            "memory_skipped_stale_or_unsupported": skipped,
            "memory_truncated": len(exchanges) > len(selected) + skipped,
        },
    )


def retrieval_question(question, previous_questions):
    if not previous_questions:
        return question
    return json.dumps({"previous_questions": previous_questions[-2:], "question": question})[:5000]
