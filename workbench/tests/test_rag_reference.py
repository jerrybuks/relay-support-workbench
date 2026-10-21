"""Real local Qdrant + actual OpenAI SDK over mock HTTP; no live quality claims."""

import copy
import json
from dataclasses import replace

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient
from openai import OpenAI
from test_contact1_live import response

from relay.models import Actor
from relay.seed import DOCUMENTS
from teaching.contact1_live import create_app
from teaching.rag_reference import RagConfig, RagFailure, VectorRag, chunks

CONFIG = RagConfig(dimensions=3, min_score=0.8)
ACTOR = Actor(workspace="test", tenant="kora", role="agent", name="test", csrf="test")
DOCS = [d for d in DOCUMENTS if d["tenant"] == "kora" and d["state"] == "published"]
TEAM = [d for d in DOCS if d["visibility"] == "team"]


def vector(text):
    # Hand-authored transport fixtures; prove semantic-vector plumbing, not OpenAI quality.
    if "chocolate cake" in text.lower() or text.lower() == "delivery policy":
        return [1.0, 1.0, 1.0]
    if any(term in text.lower() for term in ("express", "credit", "remedy", "supervisor")):
        return [1.0, 0.0, 0.0]
    if any(term in text.lower() for term in ("address", "recipient", "dispatch")):
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


@pytest.fixture(params=["openai", "openrouter"])
def sdk(request):
    requests = []
    failures = {}

    def handler(request):
        body = json.loads(request.content)
        requests.append((request.url.path, body))
        if request.url.path.endswith("embeddings"):
            if failures.get("timeout"):
                raise httpx.ReadTimeout("PRIVATE-EMBEDDING-PAYLOAD", request=request)
            vectors = [vector(t) for t in body["input"]]
            if failures.get("dimensions"):
                vectors = [[1.0] for _ in vectors]
            if failures.get("zero"):
                vectors = [[0.0, 0.0, 0.0] for _ in vectors]
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": failures.get("returned_model", CONFIG.model),
                    "data": [
                        {"object": "embedding", "index": i, "embedding": v}
                        for i, v in enumerate(vectors)
                    ],
                    "usage": {"prompt_tokens": 12, "total_tokens": 12},
                },
            )
        if "tools" in body:
            return response(
                [
                    {
                        "type": "function_call",
                        "id": "fc_rag",
                        "call_id": "call_rag",
                        "name": "get_shipment",
                        "arguments": '{"shipment_id":"KD-80421"}',
                        "status": "completed",
                    }
                ]
            )
        evidence = json.loads(body["input"][1]["content"])["evidence"]
        return response(
            [
                {
                    "id": "msg_rag",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "annotations": [],
                            "text": json.dumps(
                                {
                                    "status": "supported",
                                    "answer": "A supervisor must review the proposed credit.",
                                    "cited_ids": [evidence[0]["id"]],
                                }
                            ),
                        }
                    ],
                }
            ]
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with OpenAI(
            api_key="local-test-placeholder",
            http_client=http,
            max_retries=0,
            base_url="https://openrouter.ai/api/v1"
            if request.param == "openrouter"
            else "https://api.openai.com/v1",
        ) as client:
            yield client, requests, failures


def test_chunks_are_exact_overlapping_and_stable():
    document = TEAM[0]
    chunk_config = replace(CONFIG, chunk_size=128, overlap=24)
    pieces = chunks(document, chunk_config)
    assert len(pieces) > 1
    assert pieces == chunks(document, chunk_config)
    assert pieces[0]["start"] == 0 and pieces[-1]["end"] == len(document["text"])
    for a, b in zip(pieces, pieces[1:]):
        assert a["start"] < b["start"] < a["end"] < b["end"]
    for chunk in pieces:
        assert chunk["excerpt"] == document["text"][chunk["start"] : chunk["end"]]


def test_persistence_cache_semantic_match_and_permission_prefilter(tmp_path, sdk):
    client, requests, _ = sdk
    rag = VectorRag(client, tmp_path / "vectors", CONFIG)
    built = rag.build(DOCS)
    assert built["embedding_calls"] == 1
    rebuilt = rag.build(DOCS)
    assert rebuilt["embedding_calls"] == 0
    assert rebuilt["reused_chunks"] == built["chunks"]
    rag.close()
    rag = VectorRag(client, tmp_path / "vectors", CONFIG)
    try:
        # These query words occur in none of the indexed delivery policy words.
        hits, trace = rag.search(TEAM, "remedy", ACTOR)
        assert hits and hits[0]["id"] == "POL-DELIVERY-3"
        assert all(c["id"] != "OPS-PRIVATE-1" for c in hits)
        assert "CANARY" not in str(hits)
        assert trace["embedding_calls"] == 1 and trace["embedding_input_tokens"] == 12
        assert trace["retrieval"] == "vector" and trace["embedding_dimensions"] == 3
        assert requests[-1][1]["input"] == ["remedy"]
        # Permission filtering happens in Qdrant before LIMIT, including source removals.
        restricted = [TEAM[1]]
        assert rag.search(restricted, "remedy", ACTOR)[0] == []
    finally:
        rag.close()


def test_foreign_and_candidate_never_enter_search_scope(tmp_path, sdk):
    client, _, _ = sdk
    rag = VectorRag(client, tmp_path, CONFIG)
    foreign = copy.deepcopy(TEAM[0])
    foreign.update(id="FOREIGN", tenant="other", text="express credit supervisor CANARY")
    try:
        rag.build(DOCS + [foreign])
        hits, _ = rag.search(DOCUMENTS, "remedy", ACTOR)
        assert all(
            h["tenant"] == "kora" and h["state"] == "published" and h["visibility"] == "team"
            for h in hits
        )
        assert "CANARY" not in str(hits)
        with pytest.raises(RagFailure, match="published"):
            rag.build(DOCUMENTS)
    finally:
        rag.close()


def test_stale_index_fails_before_spending_and_rebuild_reuses_unchanged(tmp_path, sdk):
    client, requests, _ = sdk
    rag = VectorRag(client, tmp_path, CONFIG)
    try:
        original = rag.build(TEAM)
        changed = copy.deepcopy(TEAM)
        changed[0]["text"] += " Published policy update."
        before = len(requests)
        with pytest.raises(RagFailure, match="stale"):
            rag.search(changed, "remedy", ACTOR)
        assert len(requests) == before
        report = rag.build(changed)
        assert report["revision"] != original["revision"]
        assert report["reused_chunks"] > 0 and report["embedding_calls"] == 1
    finally:
        rag.close()


def test_failed_build_preserves_previous_index_and_dimension_validation(tmp_path, sdk):
    client, _, failures = sdk
    rag = VectorRag(client, tmp_path, CONFIG)
    try:
        original = rag.build(TEAM)
        changed = copy.deepcopy(TEAM)
        changed[0]["text"] += " Changed."
        failures["dimensions"] = True
        with pytest.raises(RagFailure, match="invalid_embedding_vector"):
            rag.build(changed)
        assert rag.manifest()["collection"] == original["collection"]
        failures.clear()
        assert rag.search(TEAM, "remedy", ACTOR)[0]
        rag.config = replace(CONFIG, dimensions=2)
        with pytest.raises(RagFailure, match="configuration_mismatch"):
            rag.search(TEAM, "remedy", ACTOR)
    finally:
        rag.close()


def test_hybrid_exposes_separate_rrf_and_cosine_scores(tmp_path, sdk):
    client, _, _ = sdk
    rag = VectorRag(client, tmp_path, replace(CONFIG, mode="hybrid"))
    try:
        rag.build(TEAM)
        hits, trace = rag.search(TEAM, "delivery service credit policy", ACTOR)
        assert hits[0]["id"] == "POL-DELIVERY-3"
        assert 0 < hits[0]["score"] < 0.1
        assert hits[0]["vector_score"] > 0.8
        assert trace["retrieval"] == "hybrid"
    finally:
        rag.close()


@pytest.mark.parametrize("failure", [None, "timeout", "dimensions", "zero", "missing"])
def test_full_api_embedding_qdrant_tool_structured_answer_and_fail_closed(tmp_path, sdk, failure):
    client, requests, failures = sdk
    vector_path = tmp_path / "vectors"
    if failure != "missing":
        builder = VectorRag(client, vector_path, CONFIG)
        builder.build(DOCS)
        builder.close()
    requests.clear()
    if failure:
        failures[failure] = True
    app = create_app(
        tmp_path / "cases.sqlite",
        client=client,
        model="mock-model",
        vector_path=vector_path,
        rag_config=CONFIG,
    )
    with TestClient(app, base_url="http://localhost") as browser:
        login(browser)
        status = browser.get("/api/v1/rag/status").json()
        assert status["ready"] == (failure != "missing")
        result = browser.post(
            "/api/v1/cases/RY-1042/investigations", json={"question": "What remedy is available?"}
        )
        assert result.status_code == 200
        run = result.json()
        if failure:
            assert run["status"] == "unavailable"
            assert run["citations"] == [] and run["suggested_credit_naira"] is None
            assert not any(path.endswith("responses") for path, _ in requests)
            assert "PRIVATE-EMBEDDING-PAYLOAD" not in result.text
            return
        assert run["status"] == "supported" and run["suggested_credit_naira"] == 2000
        assert [path.rsplit("/", 1)[-1] for path, _ in requests] == [
            "embeddings",
            "responses",
            "responses",
        ]
        citation = run["citations"][0]
        doc = next(d for d in TEAM if d["id"] == citation["id"])
        assert citation["chunk_id"]
        assert citation["excerpt"] == doc["text"][citation["start"] : citation["end"]]
        assert run["trace"]["embedding_calls"] == 1
        assert run["trace"]["model_calls"] == 2
        assert run["trace"]["retrieval"] == "vector"
        assert "CANARY" not in str(requests[1:])
        assert browser.get("/api/v1/cases/RY-1042").json()["proposals"] == []


def test_retrieval_inspection_requires_writer_csrf_and_never_generates(tmp_path, sdk):
    client, requests, _ = sdk
    path = tmp_path / "vectors"
    builder = VectorRag(client, path, CONFIG)
    builder.build(DOCS)
    builder.close()
    requests.clear()
    app = create_app(
        tmp_path / "cases.sqlite",
        client=client,
        model="mock-model",
        vector_path=path,
        rag_config=CONFIG,
    )
    with TestClient(app, base_url="http://localhost") as browser:
        assert browser.get("/api/v1/rag/status").status_code == 401
        login(browser)
        assert "/api/v1/rag/search" in browser.get("/openapi.json").json()["paths"]
        assert (
            browser.post(
                "/api/v1/rag/search", json={"question": "remedy"}, headers={"X-CSRF-Token": "wrong"}
            ).status_code
            == 403
        )
        result = browser.post("/api/v1/rag/search", json={"question": "remedy"})
        assert result.status_code == 200 and result.json()["hits"][0]["id"] == "POL-DELIVERY-3"
        assert "CANARY" not in result.text
        login(browser, "observer")
        assert browser.post("/api/v1/rag/search", json={"question": "remedy"}).status_code == 403
        assert len(requests) == 1 and requests[0][0].endswith("embeddings")


def test_corrupt_manifest_is_a_safe_failure(tmp_path, sdk):
    client, _, _ = sdk
    rag = VectorRag(client, tmp_path, CONFIG)
    try:
        rag.manifest_path.write_text("[]")
        with pytest.raises(RagFailure, match="missing_or_invalid"):
            rag.manifest()
    finally:
        rag.close()


def test_vector_evaluation_accounts_separate_budgets_and_retrieval_metrics(tmp_path, sdk):
    from scripts.evaluate_live import evaluate

    client, requests, _ = sdk
    rag = VectorRag(client, tmp_path, CONFIG)
    try:
        rag.build(DOCS)
        requests.clear()
        item = {
            "id": "rag-budget",
            "slice": "paraphrase",
            "question": "What remedy applies?",
            "sources": ["POL-DELIVERY-3"],
            "credit": 2000,
        }
        report = evaluate(
            client,
            "mock-model",
            {"version": "test", "review_status": "draft", "cases": [item, item]},
            max_calls=4,
            rag=rag,
            max_embedding_calls=1,
        )
        assert report["completed_cases"] == 1 and report["contract_checks_passed"] == 1
        assert report["actual_embedding_calls"] == 1 and report["actual_model_calls"] == 2
        assert report["embedding_input_tokens"] == 12
        assert report["retrieval_metrics"]["mean_source_recall_at_k"] == 1
        assert report["semantic_accuracy"] is None
        assert len(requests) == 3
    finally:
        rag.close()


def test_langchain_chunker_is_used_by_actual_embedding_index_and_search(tmp_path, sdk):
    client, _, _ = sdk
    config = replace(CONFIG, chunker="langchain", chunk_size=128, overlap=24)
    rag = VectorRag(client, tmp_path, config)
    try:
        built = rag.build(TEAM)
        assert built["settings"]["chunker"] == "langchain"
        assert built["chunks"] > len(TEAM)
        hits, _ = rag.search(TEAM, "remedy", ACTOR)
        assert hits
        for hit in hits:
            doc = next(d for d in TEAM if d["id"] == hit["id"])
            assert hit["excerpt"] == doc["text"][hit["start"] : hit["end"]]
    finally:
        rag.close()


@pytest.mark.parametrize(
    "returned_model",
    [
        "text-embedding-3-small",
        "openai/text-embedding-3-small",
        "text-embedding-3-large",
        "other/text-embedding-3-small",
    ],
)
def test_gateway_embedding_alias_is_exact_and_provider_scoped(tmp_path, sdk, returned_model):
    from teaching.provider_connection import provider_name

    client, _, controls = sdk
    controls["returned_model"] = returned_model
    rag = VectorRag(client, tmp_path, replace(CONFIG, model="openai/text-embedding-3-small"))
    try:
        accepted = returned_model == "openai/text-embedding-3-small" or (
            provider_name(client) == "openrouter" and returned_model == "text-embedding-3-small"
        )
        if accepted:
            assert rag._embed_request(["Synthetic express credit"])[0] == [1.0, 0.0, 0.0]
        else:
            with pytest.raises(RagFailure, match="embedding_model_mismatch"):
                rag._embed_request(["Synthetic express credit"])
    finally:
        rag.close()


def test_typo_query_hybrid_recovers_policy_without_lowering_vector_threshold(tmp_path, sdk):
    client, requests, _ = sdk
    rag = VectorRag(client, tmp_path, replace(CONFIG, mode="hybrid"))
    try:
        rag.build(DOCS)
        hits, trace = rag.search(DOCS, "dlivery polcy", ACTOR)
        assert hits[0]["id"] == "POL-DELIVERY-3"
        assert trace["query_normalized"] is True
        assert trace["vector_hits"] == 0  # Fixture vector misses; lexical retrieval is explicit.
        assert trace["min_vector_score"] == CONFIG.min_score
        assert requests[-1][1]["input"] == ["delivery policy"]
        assert all(h["id"] != "OPS-PRIVATE-1" for h in hits)
        assert not rag.search(DOCS, "How do I bake a chocolate cake?", ACTOR)[0]
    finally:
        rag.close()


def test_query_normalization_is_conservative_and_scoped():
    from teaching.rag_reference import search_query

    assert search_query("dlivery polcy", TEAM) == "delivery policy"
    assert search_query("delivery policy", TEAM) == "delivery policy"
    assert search_query("police", TEAM) == "police"
    assert search_query("resere", TEAM) == "resere"  # Restricted title cannot influence query.
    assert search_query("dlivery", [{**TEAM[0], "title": "delivery dliverys"}]) == "dlivery"


def test_hosted_bootstrap_reuses_vectors_and_keeps_unreviewed_sources_out(
    tmp_path, sdk, monkeypatch
):
    from scripts.serve_workshop import prepare_index

    client, requests, _ = sdk
    monkeypatch.setenv("RELAY_AI_PROVIDER", "openai")
    monkeypatch.setenv("RELAY_EMBEDDING_DIMENSIONS", "3")
    monkeypatch.setenv("RELAY_VECTOR_PATH", str(tmp_path / "hosted-index"))
    monkeypatch.setenv("RELAY_BOOTSTRAP_INDEX", "1")
    prepare_index(client)
    before = len(requests)
    prepare_index(client)
    assert len(requests) == before  # Warm starts have no new embedding call.
    rag = VectorRag(client, tmp_path / "hosted-index", replace(CONFIG, min_score=0.4))
    try:
        assert set(rag.manifest()["sources"]) == {d["id"] for d in DOCS}
        assert "POL-DRAFT-4" not in rag.manifest()["sources"]
        assert "OTHER-POL" not in rag.manifest()["sources"]
    finally:
        rag.close()
