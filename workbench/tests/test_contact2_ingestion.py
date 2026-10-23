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
from teaching.contact2.markdown_practice import ROOT, preview
from teaching.contact2.policy_store import PolicyStore
from teaching.contact2.policy_store import publish_source as ingest
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


def pdf_bytes():
    from pathlib import Path

    return (Path(__file__).parents[1] / "teaching/contact2/pdfs/collection-policy.pdf").read_bytes()


def test_pdf_extraction_preserves_rules_and_rejects_unreadable_inputs():
    from teaching.contact2.indexing.parsing import extract_pdf

    text, pages = extract_pdf(pdf_bytes())
    assert len(pages) == 1 and "seven calendar days" in text
    readable = " ".join(text.split())
    assert "notice date" in readable and "supervisor reviews" in readable
    for raw in (b"not a PDF", b"%PDF-1.7 broken", b"%PDF-" + b"x" * (2 * 1024 * 1024)):
        with pytest.raises(Problem):
            extract_pdf(raw)
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(Problem) as error:
        extract_pdf(output.getvalue())
    assert error.value.code == "pdf_needs_ocr"
    writer.encrypt("not-readable")
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(Problem) as error:
        extract_pdf(output.getvalue())
    assert error.value.code == "invalid_pdf"


@pytest.mark.parametrize("visibility", ["team", "supervisor"])
def test_pdf_ui_api_upload_review_index_real_qdrant_and_rerun(tmp_path, provider, visibility):
    sdk, calls, failure = provider
    app = create_app(
        tmp_path / "pdf.sqlite",
        client=sdk,
        model="fixture",
        vector_path=tmp_path / "vectors",
        rag_config=CONFIG,
        state="before",
    )
    with TestClient(app, base_url="http://127.0.0.1") as browser:
        url = "/api/v1/teaching/pdf?title=Parcel%20collection%20policy&visibility=" + visibility
        login(browser, "agent")
        assert (
            browser.post(
                url, content=pdf_bytes(), headers={"Content-Type": "application/pdf"}
            ).status_code
            == 403
        )
        login(browser, "supervisor")
        assert (
            browser.post(
                url,
                content=pdf_bytes(),
                headers={"Content-Type": "application/pdf", "X-CSRF-Token": "bad"},
            ).status_code
            == 403
        )
        assert (
            browser.post(
                url,
                content=b"x" * (2 * 1024 * 1024 + 1),
                headers={"Content-Type": "application/pdf"},
            ).status_code
            == 413
        )
        # The larger file allowance never applies to ordinary API bodies.
        assert browser.post("/api/v1/teaching/policies", content=b"x" * 17000).status_code == 413
        result = browser.post(url, content=pdf_bytes(), headers={"Content-Type": "application/pdf"})
        assert result.status_code == 200, result.text
        previewed = result.json()
        assert calls == [] and previewed["chunks"] and previewed["source"]["state"] == "candidate"
        path = "/api/v1/teaching/pdf/" + previewed["upload_id"]
        assert browser.post(path + "/index", json={"confirm_billable": True}).status_code == 403
        assert browser.post(path + "/review", json={"confirm_reviewed": False}).status_code == 422
        other = TestClient(app, base_url="http://127.0.0.1")
        login(other, "supervisor")
        assert other.post(path + "/review", json={"confirm_reviewed": True}).status_code == 404
        other.close()
        assert browser.post(path + "/review", json={"confirm_reviewed": True}).status_code == 200
        assert browser.post(path + "/index", json={}).status_code == 422
        result = browser.post(path + "/index", json={"confirm_billable": True})
        assert result.status_code == 200, result.text
        indexed = result.json()
        assert indexed["stored_chunks"] == len(previewed["chunks"])
        assert indexed["records"][0]["dimensions"] == 3
        vector = indexed["records"][0]["vector_preview"]
        assert sum(v * v for v in vector) == pytest.approx(1.0, abs=0.00001)
        assert indexed["records"][0]["payload"]["visibility"] == visibility
        count = len(calls)
        repeat = browser.post(path + "/index", json={"confirm_billable": True})
        assert repeat.status_code == 200 and repeat.json()["embedding_calls"] == 0
        assert len(calls) == count
        login(browser, "agent")
        result = browser.post(
            "/api/v1/rag/search", json={"question": "parcel collection seven calendar days"}
        )
        found = previewed["source"]["id"] in [h["id"] for h in result.json()["hits"]]
        assert found is (visibility == "team")
        assert browser.post(path + "/review", json={"confirm_reviewed": True}).status_code == 403
        assert browser.get("/api/v1/teaching/pdf").status_code == 403
        login(browser, "supervisor")
        listed = browser.get("/api/v1/teaching/pdf").json()["policies"]
        assert previewed["source"]["id"] in [p["id"] for p in listed]
        deletion = "/api/v1/teaching/pdf/" + previewed["source"]["id"]
        assert (
            browser.request("DELETE", deletion, json={"confirm_remove": False}).status_code == 422
        )
        assert (
            browser.request(
                "DELETE", deletion, json={"confirm_remove": True}, headers={"X-CSRF-Token": "bad"}
            ).status_code
            == 403
        )
        count = len(calls)
        result = browser.request("DELETE", deletion, json={"confirm_remove": True})
        assert result.status_code == 200 and result.json()["removed"]
        assert result.json()["embedding_calls"] == 0 and len(calls) == count
        assert browser.get("/api/v1/teaching/pdf").json()["policies"] == []
        assert previewed["source"]["id"] not in app.state.rag.manifest()["sources"]
        assert previewed["source"]["id"] not in [d["id"] for d in app.state.store.corpus()]
        assert browser.post(path + "/index", json={"confirm_billable": True}).status_code == 404
        assert (
            browser.request(
                "DELETE", "/api/v1/teaching/pdf/POL-DELIVERY-1", json={"confirm_remove": True}
            ).status_code
            == 404
        )
        uploaded_again = browser.post(
            url, content=pdf_bytes(), headers={"Content-Type": "application/pdf"}
        )
        assert uploaded_again.status_code == 200
        path = "/api/v1/teaching/pdf/" + uploaded_again.json()["upload_id"]
        browser.post(path + "/review", json={"confirm_reviewed": True})
        assert browser.post(path + "/index", json={"confirm_billable": True}).status_code == 200


def test_pdf_failed_embedding_does_not_publish_source(tmp_path, provider):
    from teaching.contact2.document_service import approve_pdf, index_pdf, stage_pdf

    sdk, calls, failure = provider
    store = PolicyStore(tmp_path / "pdf.sqlite")
    rag = VectorRag(sdk, tmp_path / "vectors", CONFIG)
    try:
        rag.build(store.corpus())
        old_revision = rag.manifest()["revision"]
        staged = stage_pdf(store, pdf_bytes(), "New collection policy", "team", ACTOR, CONFIG)
        approve_pdf(store, staged["upload_id"], ACTOR)
        failure["fail"] = True
        with pytest.raises(Exception):
            index_pdf(store, rag, staged["upload_id"], ACTOR)
        assert rag.manifest()["revision"] == old_revision
        assert staged["source"]["id"] not in [d["id"] for d in store.documents(ACTOR)]
    finally:
        rag.close()
        sdk.close()


def test_removal_preserves_other_policies_and_never_calls_provider(tmp_path, provider):
    from teaching.contact2.document_service import approve_pdf, index_pdf, remove_pdf, stage_pdf

    sdk, calls, failure = provider
    store = PolicyStore(tmp_path / "remove.sqlite")
    rag = VectorRag(sdk, tmp_path / "vectors", CONFIG)
    try:
        policies = []
        for title in ("First collection policy", "Second collection policy"):
            staged = stage_pdf(store, pdf_bytes(), title, "team", ACTOR, CONFIG)
            approve_pdf(store, staged["upload_id"], ACTOR)
            index_pdf(store, rag, staged["upload_id"], ACTOR)
            policies.append(staged["source"]["id"])
        count = len(calls)
        failure["fail"] = True
        with pytest.raises(Problem):
            remove_pdf(store, rag, policies[0], replace_actor(ACTOR, tenant="foreign"))
        with pytest.raises(Problem):
            remove_pdf(store, rag, policies[0], replace_actor(ACTOR, role="agent"))
        remove_pdf(store, rag, policies[0], ACTOR)
        assert len(calls) == count
        remaining = {d["id"] for d in store.documents(ACTOR)}
        assert policies[0] not in remaining and policies[1] in remaining
        points, _ = rag.db.scroll(rag.manifest()["collection"], limit=1000, with_payload=True)
        assert policies[0] not in {p.payload["id"] for p in points}
        assert policies[1] in {p.payload["id"] for p in points}
    finally:
        rag.close()
        sdk.close()


def test_removal_rolls_back_if_retained_vectors_are_missing(tmp_path, provider):
    from qdrant_client import models

    from teaching.contact2.document_service import approve_pdf, index_pdf, remove_pdf, stage_pdf
    from teaching.rag_reference import RagFailure

    sdk, calls, _ = provider
    store = PolicyStore(tmp_path / "remove.sqlite")
    rag = VectorRag(sdk, tmp_path / "vectors", CONFIG)
    try:
        staged = stage_pdf(store, pdf_bytes(), "Collection policy", "team", ACTOR, CONFIG)
        approve_pdf(store, staged["upload_id"], ACTOR)
        index_pdf(store, rag, staged["upload_id"], ACTOR)
        original = rag.manifest()
        points, _ = rag.db.scroll(original["collection"], limit=1000, with_payload=True)
        seed = next(p for p in points if p.payload["id"] != staged["source"]["id"])
        rag.db.delete(original["collection"], models.PointIdsList(points=[seed.id]))
        count = len(calls)
        with pytest.raises(RagFailure, match="cached_vectors_missing"):
            remove_pdf(store, rag, staged["source"]["id"], ACTOR)
        assert len(calls) == count
        assert rag.manifest()["revision"] == original["revision"]
        assert staged["source"]["id"] in {d["id"] for d in store.documents(ACTOR)}
    finally:
        rag.close()
        sdk.close()


def test_three_page_policy_fixture_keeps_rules_on_known_pages():
    from teaching.contact2.indexing.parsing import extract_pdf

    raw = (ROOT / "pdfs/collection-policy-multipage.pdf").read_bytes()
    text, pages = extract_pdf(raw)
    assert len(pages) == 3
    page_text = [" ".join(p["text"].split()) for p in pages]
    assert "seven calendar days" in page_text[0] and "notice date" in page_text[0]
    assert "collection code" in page_text[1] and "identity document" in page_text[1]
    assert "supervisor reviews" in page_text[2] and "return to the sender" in page_text[2]
    assert all(f"Page {i} of 3" in p for i, p in enumerate(page_text, 1))
    assert text == "\n\n".join(p["text"] for p in pages)
