import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .models import Actor
from .seed import CASES, DOCUMENTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, workspace TEXT NOT NULL, role TEXT NOT NULL,
 csrf TEXT NOT NULL, expires REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
 workspace TEXT NOT NULL, id TEXT NOT NULL, tenant TEXT NOT NULL, data TEXT NOT NULL,
 PRIMARY KEY(workspace,id)
);
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY, workspace TEXT NOT NULL, case_id TEXT NOT NULL,
 question TEXT NOT NULL, answer TEXT NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS proposals (
 id TEXT PRIMARY KEY, workspace TEXT NOT NULL, tenant TEXT NOT NULL, case_id TEXT NOT NULL,
 amount INTEGER NOT NULL, rationale TEXT NOT NULL, status TEXT NOT NULL,
 created REAL NOT NULL, decision_reason TEXT, proposer_role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS credits (
 proposal_id TEXT PRIMARY KEY, workspace TEXT NOT NULL, amount INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, workspace TEXT NOT NULL, event TEXT NOT NULL,
 actor TEXT NOT NULL, metadata TEXT NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency (
 workspace TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL, result TEXT NOT NULL,
 PRIMARY KEY(workspace,key)
);
CREATE TABLE IF NOT EXISTS rate_buckets (
 workspace TEXT NOT NULL, bucket INTEGER NOT NULL, count INTEGER NOT NULL,
 PRIMARY KEY(workspace,bucket)
);
"""


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)
            # Migration 2: persisted context and traces retain the originating role scope.
            # Existing local messages are conservatively restricted during upgrade.
            for table in ("messages", "audit"):
                columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
                if "visibility" not in columns:
                    db.execute(
                        f"ALTER TABLE {table} ADD COLUMN visibility TEXT NOT NULL "
                        "DEFAULT 'supervisor'"
                    )
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (2)")
            db.execute(
                "CREATE INDEX IF NOT EXISTS message_scope ON "
                "messages(workspace,case_id,visibility,id)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS audit_scope ON audit(workspace,visibility,id)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    def session(self, token: str | None):
        if not token:
            return None
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND expires>?",
                (token_hash(token), time.time()),
            ).fetchone()
        if not row:
            return None
        names = {
            "agent": "Tolu Adeyemi",
            "supervisor": "Amara Nwosu",
            "observer": "Workshop observer",
        }
        return Actor(
            workspace=row["workspace"], role=row["role"], name=names[row["role"]], csrf=row["csrf"]
        )

    def create_session(self, role, previous=None):
        old = self.session(previous)
        workspace = old.workspace if old else secrets.token_hex(12)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        with self.transaction() as db:
            if previous:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(previous),))
            db.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?)",
                (token_hash(token), workspace, role, csrf, time.time() + 8 * 3600),
            )
            for case in CASES:
                db.execute(
                    "INSERT OR IGNORE INTO cases VALUES (?,?,?,?)",
                    (workspace, case["id"], case["tenant"], encoded(case)),
                )
        return token, self.session(token)

    def cases(self, actor):
        with self.connect() as db:
            return [
                json.loads(r["data"])
                for r in db.execute(
                    "SELECT data FROM cases WHERE workspace=? AND tenant=? ORDER BY id",
                    (actor.workspace, actor.tenant),
                )
            ]

    def case(self, actor, case_id, db=None):
        if db is None:
            with self.connect() as connection:
                return self.case(actor, case_id, connection)
        row = db.execute(
            "SELECT data FROM cases WHERE workspace=? AND tenant=? AND id=?",
            (actor.workspace, actor.tenant, case_id),
        ).fetchone()
        return json.loads(row["data"]) if row else None

    def documents(self, actor):
        return [
            d.copy()
            for d in DOCUMENTS
            if d["tenant"] == actor.tenant
            and d["state"] == "published"
            and (d["visibility"] == "team" or actor.role == "supervisor")
        ]

    def audit(self, db, actor, event, metadata, visibility="team"):
        db.execute(
            "INSERT INTO audit(workspace,event,actor,metadata,created,visibility) "
            "VALUES (?,?,?,?,?,?)",
            (actor.workspace, event, actor.name, encoded(metadata), time.time(), visibility),
        )

    def timeline(self, actor):
        with self.connect() as db:
            return [
                {**dict(r), "metadata": json.loads(r["metadata"])}
                for r in db.execute(
                    "SELECT id,event,actor,metadata,created FROM audit WHERE workspace=? "
                    "AND (visibility='team' OR ?='supervisor') "
                    "ORDER BY id DESC LIMIT 100",
                    (actor.workspace, actor.role),
                )
            ]

    def messages(self, actor, case_id):
        with self.connect() as db:
            return [
                {"question": r["question"], "answer": json.loads(r["answer"])}
                for r in db.execute(
                    "SELECT question,answer FROM messages WHERE workspace=? "
                    "AND case_id=? AND (visibility='team' OR ?='supervisor') "
                    "ORDER BY id DESC LIMIT 20",
                    (actor.workspace, case_id, actor.role),
                )
            ][::-1]

    def proposals(self, actor):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM proposals WHERE workspace=? AND tenant=? ORDER BY created DESC",
                    (actor.workspace, actor.tenant),
                )
            ]

    def limited(self, actor, limit=60):
        bucket = int(time.time() // 60)
        with self.transaction() as db:
            db.execute("DELETE FROM rate_buckets WHERE bucket<?", (bucket - 2,))
            db.execute(
                "INSERT INTO rate_buckets VALUES (?,?,1) ON CONFLICT(workspace,bucket) "
                "DO UPDATE SET count=count+1",
                (actor.workspace, bucket),
            )
            return (
                db.execute(
                    "SELECT count FROM rate_buckets WHERE workspace=? AND bucket=?",
                    (actor.workspace, bucket),
                ).fetchone()[0]
                > limit
            )
