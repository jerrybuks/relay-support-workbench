"""Provider routing contracts; no network calls, credentials or live quality claims."""

import httpx
import pytest
from openai import OpenAI

from teaching.openai_state_reference import compare_state
from teaching.provider_connection import connect, model_setting, provider_name, vector_path
from teaching.rag_reference import RagConfig


def test_gateway_has_separate_credentials_endpoint_models_and_index(monkeypatch):
    monkeypatch.setenv("RELAY_AI_PROVIDER", "openrouter")
    monkeypatch.setenv("RELAY_ALLOW_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "direct-placeholder")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://untrusted.invalid")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("RELAY_VECTOR_PATH", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        connect()  # Never borrow the direct credential.
    monkeypatch.setenv("OPENROUTER_API_KEY", "gateway-placeholder")
    client, model = connect()
    with client:
        assert str(client.base_url) == "https://openrouter.ai/api/v1/"
        assert client.api_key == "gateway-placeholder"
        assert client.max_retries == 0
        assert provider_name(client) == "openrouter"
    assert model == "openai/gpt-4o"
    assert RagConfig.environment().model == "openai/text-embedding-3-small"
    assert vector_path().name == "c1-vector-openrouter"


def test_direct_route_ignores_ambient_gateway_and_base_url(monkeypatch):
    monkeypatch.setenv("RELAY_AI_PROVIDER", "openai")
    monkeypatch.setenv("RELAY_ALLOW_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "direct-placeholder")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    client, model = connect()
    with client:
        assert client.base_url.host == "api.openai.com"
        assert model == "gpt-4o"


@pytest.mark.parametrize("mode", ["previous", "conversation"])
def test_native_state_modes_rejected_before_any_gateway_request(mode):
    def forbidden(request):
        raise AssertionError("Unsupported mode must not issue a request")

    with OpenAI(
        api_key="placeholder",
        base_url="https://openrouter.ai/api/v1",
        http_client=httpx.Client(transport=httpx.MockTransport(forbidden)),
    ) as client:
        with pytest.raises(ValueError, match="requires native OpenAI"):
            compare_state(client, "openai/gpt-4o", mode)


def test_invalid_provider_and_model_fail_closed(monkeypatch):
    monkeypatch.setenv("RELAY_AI_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="RELAY_AI_PROVIDER"):
        model_setting()
    monkeypatch.setenv("RELAY_AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_MODEL", "gpt-4o")
    with pytest.raises(ValueError, match="OPENROUTER_MODEL"):
        model_setting()


def test_direct_price_card_cannot_estimate_gateway_billing():
    from teaching.cost_reference import quote_run

    with pytest.raises(ValueError, match="price_card_provider_mismatch"):
        quote_run({"provider": "openrouter"}, {"models": {}})
