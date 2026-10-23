"""Opt-in Contact 2 application. Never imported by baseline or hosted startup."""

import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, Query, Request
from fastapi.responses import FileResponse
from openai import OpenAIError
from pydantic import Field, ValidationError
from starlette.concurrency import run_in_threadpool

from relay.main import STATIC
from relay.models import Actor, Contract
from relay.service import Problem, require_writer

from .contact1_live import create_app as live_app
from .contact2 import exercise, parser_reference
from .contact2.document_service import (
    approve_pdf,
    index_pdf,
    indexed_pdfs,
    remove_pdf,
    stage_pdf,
)
from .contact2.indexing.parsing import MAX_PDF_BYTES
from .contact2.markdown_practice import preview
from .contact2.policy_store import PolicyStore
from .contact2.policy_store import publish_source as ingest
from .contact2.querying.pipeline import PolicyAnswer, answer_question
from .provider_connection import model_setting
from .rag_reference import RagFailure


class PolicyQuestion(Contract):
    question: str = Field(min_length=3, max_length=1500)


class ImportRequest(Contract):
    document: str
    execute: bool = False
    confirm_billable: bool = False


class PdfReview(Contract):
    confirm_reviewed: bool = False


class PdfIndex(Contract):
    confirm_billable: bool = False


class PdfRemoval(Contract):
    confirm_remove: bool = False


def create_app(
    db_path=None,
    *,
    client=None,
    model=None,
    vector_path=None,
    rag_config=None,
    state: Literal["before", "reference"] | None = None,
):
    state = state or os.getenv("RELAY_C2_STATE", "before")
    if state not in {"before", "reference"}:
        raise RuntimeError("Choose before or reference.")
    root = Path(os.getenv("RELAY_C2_HOME", str(Path(__file__).parents[1] / ".runtime/contact2")))
    app = live_app(
        db_path or root / "workshop.sqlite",
        client=client,
        model=model,
        vector_path=vector_path or root / "vectors",
        rag_config=rag_config,
        store_factory=PolicyStore,
        checkpoint=f"contact-2-{state}",
        session_cookie="relay_c2",
    )
    parser = exercise.parse_markdown if state == "before" else parser_reference.parse_markdown
    store, rag = app.state.store, app.state.rag
    app.state.request_body_limits = {"/api/v1/teaching/pdf": MAX_PDF_BYTES}

    def supervisor(actor: Actor = Depends(app.state.authorize)):
        if actor.role != "supervisor":
            raise Problem(403, "supervisor_required", "Use the supervisor to import a policy.")
        return actor

    @app.get("/teaching/contact-2/sample.pdf", include_in_schema=False)
    def sample_pdf():
        return FileResponse(
            Path(__file__).parent / "contact2/pdfs/collection-policy.pdf",
            media_type="application/pdf",
            filename="kora-collection-policy.pdf",
        )

    @app.get("/teaching/contact-2/sample-multipage.pdf", include_in_schema=False)
    def multi_page_sample_pdf():
        return FileResponse(
            Path(__file__).parent / "contact2/pdfs/collection-policy-multipage.pdf",
            media_type="application/pdf",
            filename="kora-collection-policy-multipage.pdf",
        )

    @app.post("/api/v1/teaching/pdf", tags=["Contact 2: PDF RAG"])
    async def upload_pdf(
        request: Request,
        title: str = Query(min_length=5, max_length=150),
        visibility: Literal["team", "supervisor"] = "team",
        actor: Actor = Depends(supervisor),
    ):
        if request.headers.get("content-type", "").split(";")[0] != "application/pdf":
            raise Problem(415, "pdf_required", "Upload a PDF document.")
        raw = await request.body()
        return await run_in_threadpool(stage_pdf, store, raw, title, visibility, actor, rag.config)

    @app.get("/api/v1/teaching/pdf", tags=["Contact 2: PDF RAG"])
    def list_pdfs(actor: Actor = Depends(supervisor)):
        return {"policies": indexed_pdfs(store, actor)}

    @app.delete("/api/v1/teaching/pdf/{source_id}", tags=["Contact 2: PDF RAG"])
    def delete_pdf(source_id: str, body: PdfRemoval, actor: Actor = Depends(supervisor)):
        if not body.confirm_remove:
            raise Problem(422, "removal_confirmation_required", "Confirm removal of this policy.")
        try:
            return remove_pdf(store, rag, source_id, actor)
        except (RagFailure, OpenAIError):
            raise Problem(
                503,
                "removal_unavailable",
                "Could not remove the policy using cached vectors. No new embeddings requested.",
            ) from None

    @app.post("/api/v1/teaching/pdf/{upload_id}/review", tags=["Contact 2: PDF RAG"])
    def review_pdf(upload_id: str, body: PdfReview, actor: Actor = Depends(supervisor)):
        if not body.confirm_reviewed:
            raise Problem(
                422,
                "review_required",
                "Confirm the extracted text is correct and permitted for teaching use.",
            )
        return approve_pdf(store, upload_id, actor)

    @app.post("/api/v1/teaching/pdf/{upload_id}/index", tags=["Contact 2: PDF RAG"])
    def build_pdf_index(upload_id: str, body: PdfIndex, actor: Actor = Depends(supervisor)):
        if not body.confirm_billable:
            raise Problem(422, "billable_confirmation_required", "Confirm the embedding request.")
        try:
            return index_pdf(store, rag, upload_id, actor)
        except (RagFailure, OpenAIError):
            raise Problem(
                503,
                "ingestion_unavailable",
                "Indexing failed. Check provider readiness and retry. Previous index retained.",
            ) from None

    @app.post(
        "/api/v1/policies/query", tags=["Contact 2: policy query"], response_model=PolicyAnswer
    )
    def query_policy(body: PolicyQuestion, actor: Actor = Depends(app.state.authorize)):
        require_writer(actor)
        try:
            return answer_question(
                store, rag, rag.client, model or model_setting(), actor, body.question
            )
        except (RagFailure, OpenAIError, ValidationError):
            raise Problem(
                503,
                "policy_query_unavailable",
                "Could not validate a policy answer. Check the index and provider, then retry.",
            ) from None

    @app.get("/teaching/contact-2", include_in_schema=False)
    def workshop():
        return FileResponse(STATIC / "contact2-lab.html")

    @app.post("/api/v1/teaching/policies", tags=["Contact 2: approved policy ingestion"])
    def policy(body: ImportRequest, actor: Actor = Depends(app.state.authorize)):
        if actor.role != "supervisor":
            raise Problem(403, "supervisor_required", "Switch to the supervisor to preview/import.")
        if body.execute and not body.confirm_billable:
            raise Problem(422, "billable_confirmation_required", "Confirm the embedding request.")
        try:
            source, passages = preview(
                body.document, parser, tenant=actor.tenant, config=rag.config
            )
            if not body.execute:
                return {
                    "source": source,
                    "chunks": passages,
                    "embedding_calls": 0,
                    "mode": "preview",
                    "checkpoint": f"contact-2-{state}",
                }
            return {"mode": "import", **ingest(store, rag, source, actor)}
        except NotImplementedError:
            raise Problem(
                501, "parser_not_implemented", "Implement exercise.parse_markdown first."
            ) from None
        except (RagFailure, OpenAIError):
            raise Problem(
                503, "ingestion_unavailable", "Import failed; inspect provider/index readiness."
            ) from None

    return app
