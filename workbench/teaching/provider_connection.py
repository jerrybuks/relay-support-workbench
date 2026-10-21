"""Explicit credential routing for opt-in references; never imported by the starter."""

import os
from pathlib import Path

ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def selected_provider():
    provider = os.getenv("RELAY_AI_PROVIDER", "openai")
    if provider not in ENDPOINTS:
        raise ValueError("RELAY_AI_PROVIDER must be openai or openrouter")
    return provider


def model_setting(*, embedding=False):
    provider = selected_provider()
    prefix = "OPENROUTER" if provider == "openrouter" else "OPENAI"
    suffix = "EMBEDDING_MODEL" if embedding else "MODEL"
    default = "text-embedding-3-small" if embedding else ""
    if provider == "openrouter":
        default = "openai/" + default if embedding else "openai/gpt-4o"
    model = os.getenv(f"{prefix}_{suffix}", default)
    if not model or (provider == "openrouter" and not model.startswith("openai/")):
        raise ValueError(f"Configure {prefix}_{suffix} with an OpenAI model ID")
    return model


def provider_name(client):
    # Identify the actual client endpoint, including injected test clients.
    return (
        "openrouter"
        if getattr(getattr(client, "base_url", None), "host", None) == "openrouter.ai"
        else "openai"
    )


def vector_path():
    root = Path(__file__).resolve().parents[1]
    suffix = "-openrouter" if selected_provider() == "openrouter" else ""
    return Path(os.getenv("RELAY_VECTOR_PATH", str(root / f".runtime/c1-vector{suffix}")))


def connect():
    from openai import OpenAI

    if os.getenv("RELAY_ALLOW_LIVE") != "1":
        raise RuntimeError("Set RELAY_ALLOW_LIVE=1 only for an authorized live smoke run.")
    provider = selected_provider()
    key_name = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
    key = os.getenv(key_name)
    if not key:
        raise RuntimeError(f"Configure {key_name} locally before starting live requests.")
    model = model_setting()
    # Explicit endpoint/key pairing prevents OPENAI_BASE_URL or another provider's
    # ambient credentials from redirecting requests. No retries or fallback billing.
    client = OpenAI(api_key=key, base_url=ENDPOINTS[provider], timeout=20, max_retries=0)
    return client, model
