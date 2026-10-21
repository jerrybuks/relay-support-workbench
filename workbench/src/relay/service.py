import hashlib
import json
import time
import uuid

from .assistant import credit_limit
from .store import encoded


class Problem(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def require_writer(actor):
    if actor.role == "observer":
        raise Problem(403, "read_only", "Observers cannot change cases or run investigations.")


def require_case(store, actor, case_id, db=None):
    case = store.case(actor, case_id, db)
    if not case:
        raise Problem(404, "case_not_found", "Case not found.")
    return case


def replay(db, actor, key, operation, payload):
    if not key or len(key) > 100:
        raise Problem(400, "idempotency_required", "Supply an Idempotency-Key of 1–100 characters.")
    fingerprint = hashlib.sha256(encoded([operation, actor.role, payload]).encode()).hexdigest()
    existing = db.execute(
        "SELECT * FROM idempotency WHERE workspace=? AND key=?", (actor.workspace, key)
    ).fetchone()
    if existing:
        if existing["fingerprint"] != fingerprint:
            raise Problem(
                409, "key_reused", "This idempotency key was used for a different request."
            )
        return fingerprint, json.loads(existing["result"])
    return fingerprint, None


def remember(db, actor, key, fingerprint, result):
    db.execute(
        "INSERT INTO idempotency VALUES (?,?,?,?)",
        (actor.workspace, key, fingerprint, encoded(result)),
    )


def propose(store, actor, case_id, data, key):
    require_writer(actor)
    with store.transaction() as db:
        case = require_case(store, actor, case_id, db)
        fingerprint, previous = replay(db, actor, key, f"propose:{case_id}", data.model_dump())
        if previous:
            return previous
        if case["version"] != data.case_version or case["status"] != "open":
            raise Problem(
                409, "stale_case", "This case changed. Refresh before proposing a credit."
            )
        limit = credit_limit(case)
        if data.amount_naira > limit:
            raise Problem(
                422, "policy_limit", f"This shipment's maximum eligible credit is ₦{limit:,}."
            )
        proposal_id = f"PR-{uuid.uuid4().hex[:10]}"
        db.execute(
            "INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                proposal_id,
                actor.workspace,
                actor.tenant,
                case_id,
                data.amount_naira,
                data.rationale,
                "pending",
                time.time(),
                None,
                actor.role,
            ),
        )
        case["status"], case["version"] = "awaiting_approval", case["version"] + 1
        db.execute(
            "UPDATE cases SET data=? WHERE workspace=? AND id=?",
            (encoded(case), actor.workspace, case_id),
        )
        result = {"id": proposal_id, "status": "pending", "amount_naira": data.amount_naira}
        store.audit(db, actor, "credit.proposed", {"case_id": case_id, **result})
        remember(db, actor, key, fingerprint, result)
        return result


def decide(store, actor, proposal_id, data, key):
    if actor.role != "supervisor":
        raise Problem(
            403, "supervisor_required", "Only a supervisor can approve or reject credits."
        )
    with store.transaction() as db:
        row = db.execute(
            "SELECT * FROM proposals WHERE workspace=? AND tenant=? AND id=?",
            (actor.workspace, actor.tenant, proposal_id),
        ).fetchone()
        if not row:
            raise Problem(404, "proposal_not_found", "Proposal not found.")
        fingerprint, previous = replay(db, actor, key, f"decide:{proposal_id}", data.model_dump())
        if previous:
            return previous
        if row["status"] != "pending":
            raise Problem(409, "already_decided", "This proposal already has a decision.")
        case = require_case(store, actor, row["case_id"], db)
        approved = data.decision == "approve"
        if approved and row["amount"] > credit_limit(case):
            raise Problem(409, "policy_changed", "Eligibility changed. Review a new proposal.")
        status = "approved" if approved else "rejected"
        db.execute(
            "UPDATE proposals SET status=?,decision_reason=? WHERE id=?",
            (status, data.reason, proposal_id),
        )
        if approved:
            # Unique proposal_id + one transaction is the local exactly-once invariant.
            # A real payment provider needs its own idempotency key/outbox integration.
            db.execute(
                "INSERT INTO credits VALUES (?,?,?)", (proposal_id, actor.workspace, row["amount"])
            )
        case["status"] = "resolved" if approved else "open"
        case["version"] += 1
        db.execute(
            "UPDATE cases SET data=? WHERE workspace=? AND id=?",
            (encoded(case), actor.workspace, case["id"]),
        )
        result = {"id": proposal_id, "status": status, "amount_naira": row["amount"]}
        store.audit(db, actor, f"credit.{status}", {"case_id": case["id"], **result})
        remember(db, actor, key, fingerprint, result)
        return result
