"""Explicit provider controls; unsupported model/settings fail at the provider boundary."""

import os


def provider_options():
    options = {}
    effort = os.getenv("OPENAI_REASONING_EFFORT")
    verbosity = os.getenv("OPENAI_VERBOSITY")
    cache_key = os.getenv("OPENAI_PROMPT_CACHE_KEY")
    if effort:
        if effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError("invalid_reasoning_setting")
        options["reasoning"] = {"effort": effort}
    if verbosity:
        if verbosity not in {"low", "medium", "high"}:
            raise ValueError("invalid_verbosity_setting")
        options["text"] = {"verbosity": verbosity}
    if cache_key:
        if len(cache_key) > 64:
            raise ValueError("invalid_cache_key")
        options["prompt_cache_key"] = cache_key
    return options
