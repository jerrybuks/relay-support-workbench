"""Document lifecycle: upload previews, source review, listing and removal.

RAG stage orchestration lives in indexing/pipeline.py. This service handles
application records and calls that pipeline after explicit supervisor review.
"""

import hashlib
import json
import time

from qdrant_client import models

from relay.service import Problem
from relay.store import encoded

from .indexing.pipeline import build_index, preview_pdf
from .policy_store import publish_source


def stage_pdf(store, raw, title, visibility, actor, config):
    fingerprint = hashlib.sha256(raw).hexdigest()
    identity = hashlib.sha256((fingerprint + title + visibility).encode()).hexdigest()
    source = {
        "id": "POL-PDF-" + identity[:16].upper(),
        "title": title,
        "version": "1.0",
        "tenant": actor.tenant,
        "visibility": visibility,
        "tags": "policy " + title,
        "state": "candidate",
    }
    source, pages, passages = preview_pdf(raw, source, config)
    upload_id = hashlib.sha256((actor.workspace + identity).encode()).hexdigest()
    with store.transaction() as db:
        db.execute("DELETE FROM c2_pdf_uploads WHERE created < ?", (time.time() - 86400,))
        count = db.execute(
            "SELECT COUNT(*) FROM c2_pdf_uploads WHERE workspace=?", (actor.workspace,)
        ).fetchone()[0]
        if (
            count >= 10
            and not db.execute("SELECT 1 FROM c2_pdf_uploads WHERE id=?", (upload_id,)).fetchone()
        ):
            raise Problem(
                429,
                "upload_limit",
                "Use up to ten policy previews per workshop workspace each day.",
            )
        db.execute(
            "INSERT OR IGNORE INTO c2_pdf_uploads VALUES (?,?,?,?,?,?,?,?)",
            (
                upload_id,
                actor.workspace,
                actor.tenant,
                fingerprint,
                encoded(source),
                None,
                None,
                time.time(),
            ),
        )
    return {
        "upload_id": upload_id,
        "sha256": fingerprint,
        "source": source,
        "pages": pages,
        "chunks": passages,
        "embedding_calls": 0,
        "chunk_settings": {
            "size_characters": config.chunk_size,
            "overlap_characters": config.overlap,
            "splitter": config.chunker,
        },
    }


def uploaded(store, upload_id, actor, db):
    row = db.execute(
        "SELECT * FROM c2_pdf_uploads WHERE id=? AND workspace=? AND tenant=? AND created>?",
        (upload_id, actor.workspace, actor.tenant, time.time() - 86400),
    ).fetchone()
    if row is None:
        raise Problem(404, "upload_not_found", "Upload this policy again in the current workspace.")
    return row


def approve_pdf(store, upload_id, actor):
    """Separate human review tied to the immutable PDF hash, not approval supplied by prose."""
    with store.transaction() as db:
        row = uploaded(store, upload_id, actor, db)
        db.execute(
            "UPDATE c2_pdf_uploads SET reviewed_by=?,reviewed_at=? WHERE id=?",
            (actor.name, time.time(), upload_id),
        )
        store.audit(db, actor, "pdf.reviewed", {"sha256": row["sha256"], "upload_id": upload_id})
    return {"approved": True, "upload_id": upload_id, "sha256": row["sha256"]}


def index_pdf(store, rag, upload_id, actor):
    """3–4. Embed passages and upsert Qdrant records using the application's real indexer."""
    with rag.lock:
        with store.connect() as db:
            row = uploaded(store, upload_id, actor, db)
            if row["reviewed_at"] is None:
                raise Problem(
                    403, "source_not_approved", "Review the extracted policy before indexing."
                )
            source = {
                **json.loads(row["source"]),
                "state": "published",
                "reviewed_by": row["reviewed_by"],
                "rights": "Supervisor confirmed permission for this local teaching import.",
            }
        report = publish_source(store, rag, source, actor)
        manifest = rag.manifest()
        points, _ = rag.db.scroll(
            manifest["collection"],
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="id", match=models.MatchValue(value=source["id"]))]
            ),
            limit=200,
            with_payload=True,
            with_vectors=True,
        )
        points.sort(key=lambda p: p.payload["start"])
        records = [
            {
                "point_id": str(p.id),
                "dimensions": len(p.vector),
                "vector_preview": p.vector[:6],
                "payload": p.payload,
            }
            for p in points
        ]
        return {
            **report,
            "source": source,
            "model": rag.config.model,
            "collection": manifest["collection"],
            "records": records,
            "stored_chunks": len(records),
        }


def indexed_pdfs(store, actor):
    """The teaching policy corpus is shared within a tenant; management is supervisor-only."""
    if actor.role != "supervisor":
        raise Problem(403, "supervisor_required", "Use the supervisor to manage teaching policies.")
    with store.connect() as db:
        return [
            {k: source[k] for k in ("id", "title", "version", "visibility")}
            for row in db.execute(
                "SELECT data FROM c2_sources WHERE tenant=? ORDER BY id", (actor.tenant,)
            )
            if (source := json.loads(row[0]))["id"].startswith("POL-PDF-")
        ]


def remove_pdf(store, rag, source_id, actor):
    """Remove one tenant-scoped PDF and rebuild using retained vectors only, never API calls."""
    if actor.role != "supervisor":
        raise Problem(403, "supervisor_required", "Use the supervisor to remove a teaching policy.")
    with rag.lock, store.ingest_lock, store.transaction() as db:
        row = db.execute(
            "SELECT data FROM c2_sources WHERE tenant=? AND id=?", (actor.tenant, source_id)
        ).fetchone()
        if row is None or not source_id.startswith("POL-PDF-"):
            raise Problem(
                404,
                "policy_not_found",
                "This indexed PDF is not available in your teaching corpus.",
            )
        db.execute("DELETE FROM c2_sources WHERE tenant=? AND id=?", (actor.tenant, source_id))
        report = build_index(rag, store.corpus(actor.tenant, db), allow_embeddings=False)
        for upload in db.execute(
            "SELECT id,source FROM c2_pdf_uploads WHERE tenant=?", (actor.tenant,)
        ).fetchall():
            if json.loads(upload["source"])["id"] == source_id:
                db.execute("DELETE FROM c2_pdf_uploads WHERE id=?", (upload["id"],))
        store.audit(db, actor, "pdf.removed", {"source_id": source_id})
    return {"removed": True, "source_id": source_id, "embedding_calls": report["embedding_calls"]}
