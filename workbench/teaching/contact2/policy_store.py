"""Canonical policy persistence and transactional publication for the teaching corpus."""

import json
import threading

from relay.seed import DOCUMENTS
from relay.service import Problem
from relay.store import Store, encoded

from .indexing.pipeline import build_index


class PolicyStore(Store):
    def __init__(self, path):
        super().__init__(path)
        self.ingest_lock = threading.RLock()
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS c2_sources "
                "(tenant TEXT,id TEXT,data TEXT,PRIMARY KEY(tenant,id))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS c2_pdf_uploads "
                "(id TEXT PRIMARY KEY,workspace TEXT,tenant TEXT,sha256 TEXT,source TEXT,"
                "reviewed_by TEXT,reviewed_at REAL,created REAL)"
            )

    def corpus(self, tenant="kora", db=None):
        if db is None:
            with self.connect() as connection:
                return self.corpus(tenant, connection)
        return [
            d.copy() for d in DOCUMENTS if d["tenant"] == tenant and d["state"] == "published"
        ] + [
            json.loads(row[0])
            for row in db.execute(
                "SELECT data FROM c2_sources WHERE tenant=? ORDER BY id", (tenant,)
            )
        ]

    def documents(self, actor):
        return [
            d
            for d in self.corpus(actor.tenant)
            if d["visibility"] == "team" or actor.role == "supervisor"
        ]


def publish_source(store, rag, source, actor):
    if actor.role != "supervisor" or actor.tenant != source["tenant"]:
        raise Problem(403, "supervisor_required", "A supervisor must confirm this local import.")
    # Shared lock order matches retrieval: vector lock, then database work.
    with rag.lock, store.ingest_lock, store.transaction() as db:
        existing = {d["id"]: d for d in store.corpus(actor.tenant, db)}
        if source["id"] in existing and existing[source["id"]] != source:
            raise Problem(409, "source_conflict", "An existing source ID cannot be replaced here.")
        reused = source["id"] in existing
        db.execute(
            "INSERT OR IGNORE INTO c2_sources VALUES (?,?,?)",
            (source["tenant"], source["id"], encoded(source)),
        )
        report = build_index(rag, store.corpus(actor.tenant, db))
        store.audit(db, actor, "source.imported", {"source_id": source["id"], "reused": reused})
    return {
        "source_id": source["id"],
        "source_version": source["version"],
        "unchanged": reused,
        "chunks": report["chunks"],
        "reused_chunks": report["reused_chunks"],
        "embedding_calls": report["embedding_calls"],
        "embedding_input_tokens": report["embedding_input_tokens"],
        "revision": report["revision"],
    }
