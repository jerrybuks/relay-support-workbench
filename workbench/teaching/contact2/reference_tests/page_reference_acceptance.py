"""Opt-in live-task acceptance: red before the page-reference exercise, green afterward.

Uses original synthetic PDFs, fixture HTTP and disposable databases; no provider calls.
Run explicitly; this intentionally is not part of the green starter test suite.
"""

import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import OpenAI

from teaching.contact2.indexing.chunking import chunks
from teaching.contact2.indexing.parsing import extract_pdf
from teaching.contact2.indexing.pipeline import preview_pdf
from teaching.contact2_app import create_app
from teaching.rag_reference import RagConfig

PDF = Path(__file__).parents[1] / "pdfs/collection-policy-multipage.pdf"
META = {
    "id": "POL-PDF-PAGES",
    "title": "Collection policy",
    "version": "1.0",
    "tenant": "kora",
    "visibility": "team",
    "state": "published",
    "tags": "collection",
}


@pytest.mark.parametrize("chunker", ["native", "langchain"])
def test_original_page_ranges_and_passages_are_exact(chunker):
    config = replace(RagConfig(), chunker=chunker, chunk_size=160, overlap=32)
    text, pages = extract_pdf(PDF.read_bytes())
    source, _, passages = preview_pdf(PDF.read_bytes(), META, config)
    assert source["text"] == text == "\n\n".join(p["text"] for p in pages)
    assert len(source["page_ranges"]) == 3
    for page, span in zip(pages, source["page_ranges"], strict=True):
        assert text[span["start"] : span["end"]] == page["text"]
    for passage in passages:
        assert passage["excerpt"] == text[passage["start"] : passage["end"]]
        expected = [
            p["page"]
            for p in source["page_ranges"]
            if p["start"] < passage["end"] and passage["start"] < p["end"]
        ]
        assert passage["pages"] == expected
    second = source["page_ranges"][1]
    assert any(
        p["pages"] == [2] and second["start"] <= p["start"] < p["end"] <= second["end"]
        for p in passages
    )


def test_native_passage_crossing_page_boundary_reports_both_pages():
    source, _, passages = preview_pdf(PDF.read_bytes(), META, RagConfig())
    boundary = source["page_ranges"][0]["end"]
    spanning = [p for p in passages if p["start"] < boundary and p["end"] > boundary + 2]
    assert spanning and spanning[0]["pages"] == [1, 2]


def test_page_metadata_changes_source_identity_but_plain_sources_stay_compatible():
    from teaching.contact2.config import source_hash

    source, _, _ = preview_pdf(PDF.read_bytes(), META, RagConfig())
    changed = {**source, "page_ranges": [{"page": 99, "start": 0, "end": len(source["text"])}]}
    assert source_hash(source) != source_hash(changed)
    plain = {k: v for k, v in source.items() if k != "page_ranges"}
    assert source_hash(plain) == source_hash(dict(plain))


def test_pages_survive_storage_retrieval_and_validated_api_citation(tmp_path):
    config = replace(RagConfig(), dimensions=3, chunk_size=160, overlap=32, top_k=10, min_score=0.8)
    _, _, preview = preview_pdf(PDF.read_bytes(), META, config)
    pdf_texts = {p["excerpt"] for p in preview}
    chosen = {}

    def handler(request):
        body = json.loads(request.content)
        if request.url.path.endswith("embeddings"):
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": config.model,
                    "data": [
                        {
                            "object": "embedding",
                            "index": i,
                            "embedding": [1.0, 0.0, 0.0]
                            if t in pdf_texts or t == "recipient identification"
                            else [0.0, 1.0, 0.0],
                        }
                        for i, t in enumerate(body["input"])
                    ],
                    "usage": {"prompt_tokens": 10, "total_tokens": 10},
                },
            )
        evidence = json.loads(body["input"][1]["content"])["evidence"]
        assert chosen["id"] in {e["id"] for e in evidence}
        return httpx.Response(
            200,
            json={
                "id": "response_pages",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": "fixture-model",
                "output": [
                    {
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
                                        "answer": "Present the collection code and matching ID.",
                                        "cited_ids": [chosen["id"]],
                                    }
                                ),
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 100, "output_tokens": 25, "total_tokens": 125},
            },
        )

    sdk = OpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    app = create_app(
        tmp_path / "pages.sqlite",
        client=sdk,
        model="fixture-model",
        vector_path=tmp_path / "vectors",
        rag_config=config,
    )
    try:
        with TestClient(app, base_url="http://127.0.0.1") as browser:
            session = browser.post("/api/v1/demo/session", json={"role": "supervisor"}).json()
            browser.headers["X-CSRF-Token"] = session["csrf_token"]
            staged = browser.post(
                "/api/v1/teaching/pdf?title=Collection%20policy",
                content=PDF.read_bytes(),
                headers={"Content-Type": "application/pdf"},
            ).json()
            path = "/api/v1/teaching/pdf/" + staged["upload_id"]
            assert (
                browser.post(path + "/review", json={"confirm_reviewed": True}).status_code == 200
            )
            indexed = browser.post(path + "/index", json={"confirm_billable": True})
            assert indexed.status_code == 200, indexed.text
            points, _ = app.state.rag.db.scroll(app.state.rag.manifest()["collection"], limit=1000)
            second = next(p for p in points if p.payload.get("pages") == [2])
            chosen["id"] = str(second.id)
            source = next(d for d in app.state.store.corpus() if d["id"] == staged["source"]["id"])
            assert source["page_ranges"] == staged["source"]["page_ranges"]
            assert any(p["pages"] == [2] for p in chunks(source, config))
            result = browser.post(
                "/api/v1/policies/query", json={"question": "recipient identification"}
            )
            assert result.status_code == 200, result.text
            assert result.json()["citations"][0]["pages"] == [2]
            assert any(p["pages"] == [2] for p in result.json()["retrieved_passages"])
    finally:
        sdk.close()
