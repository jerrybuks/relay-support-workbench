"""Usage-based token cost estimates from an explicitly dated, supplied price card."""

import json
import math
from datetime import date
from pathlib import Path


def load_price_card(path):
    card = json.loads(Path(path).read_text())
    if card.get("currency") != "USD" or not card.get("version") or not card.get("source_url"):
        raise ValueError("invalid_price_card")
    date.fromisoformat(card["as_of"])
    for rates in card["models"].values():
        for value in rates.values():
            if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
                raise ValueError("invalid_price_card_rate")
    return card


def quote_run(run, card):
    if run.get("provider", "openai") != card.get("provider", "openai"):
        raise ValueError("price_card_provider_mismatch")
    trace = run["trace"]
    total = 0
    if trace.get("model_calls"):
        if trace.get("input_tokens") is None or trace.get("output_tokens") is None:
            raise ValueError("generation_usage_incomplete")
        rates = card["models"][run["model"]]
        cached = trace.get("cached_input_tokens", 0)
        if not 0 <= cached <= trace["input_tokens"]:
            raise ValueError("invalid_cached_usage")
        total += (
            (trace["input_tokens"] - cached) * rates["input"]
            + cached * rates["cached_input"]
            + trace["output_tokens"] * rates["output"]
        )
    if trace.get("embedding_calls"):
        if trace.get("embedding_input_tokens") is None:
            raise ValueError("embedding_usage_incomplete")
        total += trace["embedding_input_tokens"] * card["models"][trace["embedding_model"]]["input"]
    return {
        "estimated_usd": round(total / 1_000_000, 10),
        "price_card_version": card["version"],
        "as_of": card["as_of"],
        "source_url": card["source_url"],
        "scope": "token usage only; estimate, not a provider invoice",
    }
