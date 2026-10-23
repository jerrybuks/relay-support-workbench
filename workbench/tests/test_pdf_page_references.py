"""PDF provenance through real local stores and SDK HTTP fixtures; no provider calls."""

import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from conftest import login
from fastapi.testclient import TestClient
from openai import OpenAI
from test_contact1_live import response

from relay.models import Citation
from teaching.contact2.config import digest, source_hash
from teaching.contact2.indexing.chunking import pages_for_span
from teaching.contact2.indexing.parsing import extract_pdf
from teaching.contact2_app import create_app
from teaching.rag_reference import RagConfig

PDF = Path(__file__).parents[1] / "teaching/contact2/pdfs/collection-policy-multipage.pdf"


@pytest.mark.parametrize(
    "start,end,expected",
    [(0, 3, [1]), (3, 5, []), (5, 8, [2]), (2, 6, [1, 2]), (0, 5, [1]), (3, 8, [2])],
)
def test_page_overlap_excludes_separators_and_touching_boundaries(start, end, expected):
    source = {
        "page_ranges": [
            {"page": 1, "start": 0, "end": 3},
            {"page": 2, "start": 5, "end": 8},
        ]
    }
    assert pages_for_span(source, start, end) == expected


def test_plain_sources_retain_legacy_identity_and_citation_fields():
    plain = {"id": "plain", "text": "Unchanged text", "tenant": "kora"}
    assert source_hash(plain) == digest(
        {
            k: plain.get(k)
            for k in ("id", "tenant", "title", "version", "text", "tags", "state", "visibility")
        }
    )
    assert pages_for_span(plain, 0, 5) == []
    citation = Citation(id="plain", title="Policy", version="1", excerpt=plain["text"])
    assert citation.pages == []


@pytest.mark.parametrize("chunk_size,expected_pages", [(160, [2]), (320, [1, 2])])
def test_pdf_pages_survive_index_retrieval_and_citation(tmp_path, chunk_size, expected_pages):
    chosen = {}

    def handler(request):
        body = json.loads(request.content)
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": "text-embedding-3-small",
                    "data": [
                        {
                            "object": "embedding",
                            "index": i,
                            "embedding": [1.0, 0.0, 0.0]
                            if text in {chosen["excerpt"], "recipient identification"}
                            else [0.0, 1.0, 0.0],
                        }
                        for i, text in enumerate(body["input"])
                    ],
                    "usage": {"prompt_tokens": 10, "total_tokens": 10},
                },
            )
        evidence = json.loads(body["input"][1]["content"])["evidence"]
        assert [p["id"] for p in evidence] == [chosen["chunk_id"]]
        return response(
            [
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
                                    "answer": "Use the collection code and matching ID.",
                                    "cited_ids": [chosen["chunk_id"]],
                                }
                            ),
                        }
                    ],
                }
            ]
        )

    config = replace(RagConfig(), dimensions=3, chunk_size=chunk_size, overlap=32, min_score=0.8)
    with OpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as sdk:
        app = create_app(
            tmp_path / "pages.sqlite",
            client=sdk,
            model="fixture-model",
            vector_path=tmp_path / "vectors",
            rag_config=config,
        )
        with TestClient(app, base_url="http://127.0.0.1") as browser:
            login(browser, "supervisor")
            raw = PDF.read_bytes()
            text, pages = extract_pdf(raw)
            staged = browser.post(
                "/api/v1/teaching/pdf?title=Collection%20page%20regression",
                content=raw,
                headers={"Content-Type": "application/pdf"},
            ).json()
            assert staged["source"]["text"] == text
            first_end = len(pages[0]["text"])
            second_start = first_end + 2
            second_end = second_start + len(pages[1]["text"])
            chosen.update(
                next(
                    p
                    for p in staged["chunks"]
                    if second_start <= p["start"] < p["end"] <= second_end
                )
                if expected_pages == [2]
                else next(
                    p
                    for p in staged["chunks"]
                    if p["start"] < first_end and second_start < p["end"] <= second_end
                )
            )
            path = "/api/v1/teaching/pdf/" + staged["upload_id"]
            assert browser.post(path + "/index", json={"confirm_billable": True}).status_code == 403
            assert (
                browser.post(path + "/review", json={"confirm_reviewed": True}).status_code == 200
            )
            indexed = browser.post(path + "/index", json={"confirm_billable": True})
            assert indexed.status_code == 200, indexed.text
            stored = next(
                r["payload"]
                for r in indexed.json()["records"]
                if r["payload"]["excerpt"] == chosen["excerpt"]
            )
            assert stored.get("pages") == expected_pages
            chosen.update(stored)
            canonical = next(
                d for d in app.state.store.corpus() if d["id"] == staged["source"]["id"]
            )
            assert canonical["page_ranges"] == staged["source"]["page_ranges"]
            result = browser.post(
                "/api/v1/policies/query",
                json={"question": "recipient identification"},
            )
            assert result.status_code == 200, result.text
            data = result.json()
            assert data["citations"] == data["retrieved_passages"]
            assert data["citations"][0]["pages"] == expected_pages
            assert data["citations"][0]["excerpt"] == text[chosen["start"] : chosen["end"]]


def test_reupload_of_legacy_preview_persists_pages_and_requires_fresh_review(tmp_path):
    import hashlib
    import time

    from relay.models import Actor
    from teaching.contact2.document_service import stage_pdf
    from teaching.contact2.policy_store import PolicyStore

    store = PolicyStore(tmp_path / "legacy-preview.sqlite")
    actor = Actor(
        workspace="fixture", tenant="kora", role="supervisor", name="reviewer", csrf="fixture"
    )
    raw, title, visibility = PDF.read_bytes(), "Collection policy", "team"
    staged = stage_pdf(store, raw, title, visibility, actor, RagConfig())
    legacy_source = {k: v for k, v in staged["source"].items() if k != "page_ranges"}
    fingerprint = hashlib.sha256(raw).hexdigest()
    identity = hashlib.sha256((fingerprint + title + visibility).encode()).hexdigest()
    legacy_id = hashlib.sha256((actor.workspace + identity).encode()).hexdigest()
    with store.transaction() as db:
        db.execute("DELETE FROM c2_pdf_uploads")
        db.execute(
            "INSERT INTO c2_pdf_uploads VALUES (?,?,?,?,?,?,?,?)",
            (
                legacy_id,
                actor.workspace,
                actor.tenant,
                fingerprint,
                json.dumps(legacy_source),
                "prior reviewer",
                time.time(),
                time.time(),
            ),
        )
    uploaded = stage_pdf(store, raw, title, visibility, actor, RagConfig())
    with store.connect() as db:
        row = db.execute(
            "SELECT * FROM c2_pdf_uploads WHERE id=?", (uploaded["upload_id"],)
        ).fetchone()
        assert json.loads(row["source"]) == uploaded["source"]
        assert len(json.loads(row["source"])["page_ranges"]) == 3
        assert row["reviewed_at"] is None and row["reviewed_by"] is None
        old = db.execute("SELECT source FROM c2_pdf_uploads WHERE id=?", (legacy_id,)).fetchone()
        assert json.loads(old["source"]) == legacy_source
