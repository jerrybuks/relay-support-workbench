"""Prepared plumbing: scoped canonical storage, trusted review record, atomic index build.

This is a local course corpus shared across workspaces within one tenant. It accepts
only packaged fixtures, not arbitrary uploads. Publication workflow remains Contact 3.
"""

import hashlib
import json
import threading
from pathlib import Path

from relay.seed import DOCUMENTS
from relay.service import Problem
from relay.store import Store, encoded

from ..rag_reference import chunks

ROOT = Path(__file__).parent


class PolicyStore(Store):
    def __init__(self, path):
        super().__init__(path)
        self.ingest_lock = threading.RLock()
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS c2_sources "
                "(tenant TEXT,id TEXT,data TEXT,PRIMARY KEY(tenant,id))"
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


def preview(name, parser, *, tenant="kora", config=None):
    # Filename allowlist prevents traversal, symlink and arbitrary-file access.
    available = {p.name: p for p in (ROOT / "policies").glob("*.md") if not p.is_symlink()}
    if name not in available:
        raise Problem(404, "policy_not_found", "Select a packaged teaching policy.")
    raw = available[name].read_bytes()
    source = parser(raw)
    approvals = json.loads((ROOT / "approvals.json").read_text())
    review = approvals.get(name, {})
    if source["tenant"] != tenant:
        raise Problem(403, "source_tenant_denied", "Source is outside this tenant.")
    if not (
        review.get("status") == "approved"
        and review.get("sha256") == hashlib.sha256(raw).hexdigest()
        and review.get("source_id") == source["id"]
        and review.get("tenant") == source["tenant"]
        and review.get("version") == source["version"]
        and review.get("visibility") == source["visibility"]
    ):
        raise Problem(403, "source_not_approved", "A separate matching review record is required.")
    source.update(reviewed_by=review["reviewed_by"], rights=review["rights"])
    from ..rag_reference import RagConfig

    return source, chunks(source, config or RagConfig())


def ingest(store, rag, source, actor):
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
        report = rag.build(store.corpus(actor.tenant, db))
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
