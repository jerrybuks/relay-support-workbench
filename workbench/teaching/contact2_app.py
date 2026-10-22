"""Opt-in Contact 2 application. Never imported by baseline or hosted startup."""

import os
from pathlib import Path
from typing import Literal

from fastapi import Depends
from fastapi.responses import FileResponse
from openai import OpenAIError

from relay.main import STATIC
from relay.models import Actor, Contract
from relay.service import Problem

from .contact1_live import create_app as live_app
from .contact2 import exercise, parser_reference
from .contact2.pipeline import PolicyStore, ingest, preview
from .rag_reference import RagFailure


class ImportRequest(Contract):
    document: str
    execute: bool = False
    confirm_billable: bool = False


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
