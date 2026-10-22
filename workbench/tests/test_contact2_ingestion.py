"""C2 uses a real local vector store with disclosed SDK transport fixtures."""

import json

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient
from openai import OpenAI

from relay.models import Actor
from relay.service import Problem
from teaching.contact2 import parser_reference
from teaching.contact2.acceptance import check
from teaching.contact2.pipeline import ROOT, PolicyStore, ingest, preview
from teaching.contact2_app import create_app
from teaching.rag_reference import RagConfig, VectorRag

CONFIG = RagConfig(model="text-embedding-3-small", dimensions=3, min_score=0.0, mode="hybrid")
ACTOR = Actor(
    workspace="fixture", tenant="kora", role="supervisor", name="reviewer", csrf="fixture"
)


@pytest.fixture
def provider():
    calls = []
    failure = {}

    def handler(request):
        calls.append(json.loads(request.content))
        if failure.get("fail"):
            raise httpx.ReadTimeout("PRIVATE_PROVIDER_ERROR", request=request)
        body = calls[-1]
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": CONFIG.model,
                "data": [
                    {"object": "embedding", "index": i, "embedding": [1.0, 0.2, 0.1]}
                    for i, _ in enumerate(body["input"])
                ],
                "usage": {"prompt_tokens": 10, "total_tokens": 10},
            },
        )

    return (
        OpenAI(
            api_key="fixture",
            base_url="https://api.openai.com/v1",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            max_retries=0,
        ),
        calls,
        failure,
    )


def test_reference_passes_independent_exercise_acceptance():
    assert check(parser_reference.parse_markdown) == {
        "status": "passed",
        "checks": 16,
        "provider_calls": 0,
    }


def test_reference_parser_preserves_canonical_text():
    raw = (ROOT / "policies/collection.md").read_bytes()
    source = parser_reference.parse_markdown(raw)
    assert "seven calendar days" in source["text"]
    assert source["text"] == raw.decode().split("\n---\n", 1)[1]


@pytest.mark.parametrize(
    "raw",
    [
        b"\xff",
        b"# no metadata",
        b"",
        b"x" * 12001,
        b'---\n{"id":"POL-TEST-1","approved":true}\n---\n' + b"x" * 60,
    ],
)
def test_malformed_inputs_fail_closed(raw):
    with pytest.raises(Problem) as error:
        parser_reference.parse_markdown(raw)
    assert error.value.code == "invalid_policy"


@pytest.mark.parametrize(
    "name", ["missing-metadata.md", "unreviewed.md", "injection.md", "../../.env", "/etc/passwd"]
)
def test_unreviewed_injected_invalid_and_traversal_are_rejected(name):
    with pytest.raises(Problem):
        preview(name, parser_reference.parse_markdown)


def test_document_cannot_change_approval_or_tenant():
    def tamper(raw):
        source = parser_reference.parse_markdown(raw)
        source["visibility"] = "supervisor"
        return source

    with pytest.raises(Problem, match="matching review"):
        preview("collection.md", tamper)
    with pytest.raises(Problem) as error:
        preview("collection.md", parser_reference.parse_markdown, tenant="other")
    assert error.value.code == "source_tenant_denied"


def test_canonical_storage_index_reuse_conflict_and_failure_rollback(tmp_path, provider):
    sdk, calls, failure = provider
    store = PolicyStore(tmp_path / "test.sqlite")
    rag = VectorRag(sdk, tmp_path / "vectors", CONFIG)
    try:
        rag.build(store.corpus())
        source, _ = preview("collection.md", parser_reference.parse_markdown, config=CONFIG)
        first = ingest(store, rag, source, ACTOR)
        count = len(calls)
        second = ingest(store, rag, source, ACTOR)
        assert second["embedding_calls"] == 0 and len(calls) == count
        assert second["unchanged"] and second["reused_chunks"] == first["chunks"]
        assert sum(d["id"] == source["id"] for d in store.documents(ACTOR)) == 1
        hits, _ = rag.search(store.documents(ACTOR), "parcel collection seven calendar days", ACTOR)
        assert any(h["id"] == source["id"] for h in hits)
        with pytest.raises(Problem) as error:
            ingest(store, rag, {**source, "text": "conflicting body"}, ACTOR)
        assert error.value.code == "source_conflict" and len(calls) == count + 1
        old_revision = rag.manifest()["revision"]
        failure["fail"] = True
        other = preview("redelivery.md", parser_reference.parse_markdown, config=CONFIG)[0]
        with pytest.raises(Exception):
            ingest(store, rag, other, ACTOR)
        assert rag.manifest()["revision"] == old_revision
        assert not any(d["id"] == other["id"] for d in store.documents(ACTOR))
    finally:
        rag.close()
        sdk.close()


def test_restricted_source_never_leaks_via_vector_or_lexical_results(tmp_path, provider):
    sdk, _, _ = provider
    store = PolicyStore(tmp_path / "test.sqlite")
    rag = VectorRag(sdk, tmp_path / "vectors", CONFIG)
    try:
        source = preview("restricted.md", parser_reference.parse_markdown, config=CONFIG)[0]
        ingest(store, rag, source, ACTOR)
        agent = replace_actor(ACTOR, role="agent")
        assert source["id"] not in [d["id"] for d in store.documents(agent)]
        hits, _ = rag.search(
            store.documents(agent), "COLLECTION-REVIEW-7 collection supervisor", agent
        )
        assert source["id"] not in [h["id"] for h in hits]
        assert source["id"] not in [d["id"] for d in store.corpus("foreign")]
    finally:
        rag.close()
        sdk.close()


def replace_actor(actor, **values):
    return actor.model_copy(update=values)


@pytest.mark.parametrize("state", ["before", "reference"])
def test_lab_api_permissions_preview_confirm_and_live_search(tmp_path, provider, state):
    sdk, calls, failure = provider
    app = create_app(
        tmp_path / "app.sqlite",
        client=sdk,
        model="fixture",
        vector_path=tmp_path / "vectors",
        rag_config=CONFIG,
        state=state,
    )
    with TestClient(app, base_url="http://127.0.0.1") as browser:
        assert browser.get("/teaching/contact-2").status_code == 200
        assert (
            browser.post(
                "/api/v1/teaching/policies", json={"document": "collection.md"}
            ).status_code
            == 401
        )
        login(browser, "agent")
        assert (
            browser.post(
                "/api/v1/teaching/policies", json={"document": "collection.md"}
            ).status_code
            == 403
        )
        login(browser, "supervisor")
        payload = {"document": "collection.md"}
        response = browser.post("/api/v1/teaching/policies", json=payload)
        assert len(calls) == 0
        if state == "before":
            assert (
                response.status_code == 501
                and response.json()["error"]["code"] == "parser_not_implemented"
            )
            return
        assert response.status_code == 200 and response.json()["chunks"]
        assert (
            browser.post("/api/v1/teaching/policies", json={**payload, "execute": True}).status_code
            == 422
        )
        assert (
            browser.post(
                "/api/v1/teaching/policies", json=payload, headers={"X-CSRF-Token": "bad"}
            ).status_code
            == 403
        )
        response = browser.post(
            "/api/v1/teaching/policies", json={**payload, "execute": True, "confirm_billable": True}
        )
        assert response.status_code == 200
        result = browser.post(
            "/api/v1/rag/search", json={"question": "parcel collection seven calendar days"}
        )
        assert any(h["id"] == "POL-COLLECTION-1" for h in result.json()["hits"])
        failure["fail"] = True
        response = browser.post(
            "/api/v1/teaching/policies",
            json={"document": "redelivery.md", "execute": True, "confirm_billable": True},
        )
        assert response.status_code == 503 and "PRIVATE" not in response.text
