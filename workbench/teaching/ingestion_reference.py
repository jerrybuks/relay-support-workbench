"""Contact 3: local untrusted candidate → explicit reviewed publication."""

import hashlib
import json
import re
import time
from html.parser import HTMLParser

from fastapi import Depends
from pydantic import Field

from relay.main import create_app as baseline
from relay.models import Actor, Contract
from relay.seed import DOCUMENTS
from relay.service import Problem, require_writer
from relay.store import Store, encoded

from .contact1_reference import search_reference


class CandidateInput(Contract):
    source_id: str = Field(pattern=r"^POL-[A-Z0-9-]{3,40}$")
    title: str = Field(min_length=5, max_length=150)
    html: str = Field(min_length=30, max_length=8000)
    license_notes: str = Field(min_length=10, max_length=300)
    provenance: str = Field(min_length=10, max_length=300)


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text)


def parse_candidate(data):
    parser = TextOnly()
    parser.feed(data.html)
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    if len(text) < 30:
        raise Problem(
            422, "empty_source", "Candidate needs at least 30 characters of readable text."
        )
    return {
        "id": data.source_id,
        "title": data.title,
        "text": text,
        "version": "candidate-1",
        "visibility": "team",
        "state": "candidate",
        "tags": "",
        "provenance": data.provenance,
        "license_notes": data.license_notes,
        "content_hash": hashlib.sha256(text.encode()).hexdigest(),
        "reviewed_by": None,
    }


class ReviewStore(Store):
    def __init__(self, path):
        super().__init__(path)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS candidates (workspace TEXT,id TEXT,hash TEXT,"
                "data TEXT,PRIMARY KEY(workspace,id),UNIQUE(workspace,hash))"
            )

    def documents(self, actor):
        existing = super().documents(actor)
        with self.connect() as db:
            values = [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT data FROM candidates WHERE workspace=?", (actor.workspace,)
                )
            ]
        return existing + [
            d for d in values if d["state"] == "published" and d["tenant"] == actor.tenant
        ]


def create_app(db_path=None):
    import os
    from pathlib import Path

    path = db_path or os.getenv(
        "RELAY_REFERENCE_DB", str(Path(__file__).parents[1] / ".runtime/c3.sqlite")
    )
    app = baseline(
        path,
        retriever=search_reference,
        checkpoint="contact-3-ingestion-reference",
        store_factory=ReviewStore,
    )
    store, authorize = app.state.store, app.state.authorize

    @app.post("/api/v1/review/candidates", tags=["Reference: review queue"])
    def submit(data: CandidateInput, identity: Actor = Depends(authorize)):
        require_writer(identity)
        candidate = parse_candidate(data)
        candidate["tenant"] = identity.tenant
        with store.transaction() as db:
            base_ids = {d["id"] for d in DOCUMENTS if d["tenant"] == identity.tenant}
            duplicate = db.execute(
                "SELECT 1 FROM candidates WHERE workspace=? AND (id=? OR hash=?)",
                (identity.workspace, candidate["id"], candidate["content_hash"]),
            ).fetchone()
            if candidate["id"] in base_ids or duplicate:
                raise Problem(
                    409, "duplicate_source", "That source ID or content is already present."
                )
            db.execute(
                "INSERT INTO candidates VALUES (?,?,?,?)",
                (
                    identity.workspace,
                    candidate["id"],
                    candidate["content_hash"],
                    encoded(candidate),
                ),
            )
            store.audit(db, identity, "source.queued", {"source_id": candidate["id"]})
        return candidate

    @app.get("/api/v1/review/candidates", tags=["Reference: review queue"])
    def queue(identity: Actor = Depends(authorize)):
        if identity.role != "supervisor":
            raise Problem(
                403, "supervisor_required", "Only supervisors can inspect the review queue."
            )
        with store.connect() as db:
            return {
                "items": [
                    json.loads(row[0])
                    for row in db.execute(
                        "SELECT data FROM candidates WHERE workspace=?", (identity.workspace,)
                    )
                ]
            }

    @app.post("/api/v1/review/candidates/{source_id}/publish", tags=["Reference: review queue"])
    def publish(source_id: str, identity: Actor = Depends(authorize)):
        if identity.role != "supervisor":
            raise Problem(
                403, "supervisor_required", "A supervisor must review before publication."
            )
        with store.transaction() as db:
            row = db.execute(
                "SELECT data FROM candidates WHERE workspace=? AND id=?",
                (identity.workspace, source_id),
            ).fetchone()
            if not row:
                raise Problem(404, "source_not_found", "Candidate not found.")
            candidate = json.loads(row[0])
            if candidate["state"] != "candidate":
                raise Problem(409, "already_published", "Source already published.")
            candidate.update(
                state="published", version="1.0", reviewed_by=identity.name, reviewed_at=time.time()
            )
            db.execute(
                "UPDATE candidates SET data=? WHERE workspace=? AND id=?",
                (encoded(candidate), identity.workspace, source_id),
            )
            store.audit(
                db,
                identity,
                "source.published",
                {"source_id": source_id, "content_hash": candidate["content_hash"]},
            )
        return candidate

    return app
