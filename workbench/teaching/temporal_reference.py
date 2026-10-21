"""Opt-in durable workflow reference; never starts a service/schedule at import.

Signals must come from an authenticated backend after role/CSRF/approval checks.
The local Temporal test server is not a production authorization system.
"""

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleCalendarSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleRange,
    ScheduleSpec,
)
from temporalio.common import RetryPolicy


@activity.defn
def record_credit(proposal: dict) -> dict:
    import sqlite3

    with sqlite3.connect(proposal["ledger_path"]) as db:
        db.execute("CREATE TABLE IF NOT EXISTS effects (id TEXT PRIMARY KEY, amount INTEGER)")
        db.execute(
            "INSERT OR IGNORE INTO effects VALUES (?,?)", (proposal["id"], proposal["amount_naira"])
        )
        amount = db.execute("SELECT amount FROM effects WHERE id=?", (proposal["id"],)).fetchone()[
            0
        ]
        if amount != proposal["amount_naira"]:
            raise ValueError("Conflicting activity retry")
    return {"id": proposal["id"], "amount_naira": amount, "status": "recorded-local-only"}


@workflow.defn
class CreditApproval:
    def __init__(self):
        self.review = None
        self.proposal_id = None

    @workflow.signal
    def review_proposal(self, decision: dict):
        if (
            self.review is None
            and decision.get("role") == "supervisor"
            and decision.get("proposal_id") == self.proposal_id
            and decision.get("decision") in {"approve", "reject"}
        ):
            self.review = decision

    @workflow.query
    def status(self) -> str:
        return "review_received" if self.review else "awaiting_review"

    @workflow.run
    async def run(self, proposal: dict) -> dict:
        self.proposal_id = proposal["id"]
        await workflow.wait_condition(
            lambda: self.review is not None, timeout=timedelta(minutes=30)
        )
        if self.review["decision"] == "reject":
            return {"status": "rejected", "id": proposal["id"]}
        return await workflow.execute_activity(
            record_credit,
            proposal,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3, non_retryable_error_types=["ValueError"]),
        )


@workflow.defn
class PolicyFreshness:
    @workflow.run
    async def run(self, source_version: str) -> dict:
        # Synthetic inspection only; no external crawling or source publication.
        return {
            "status": "review_required",
            "source_version": source_version,
            "mode": "local-fixture",
            "run_id": workflow.info().workflow_id,
        }


def freshness_schedule() -> Schedule:
    """A definition for inspection; no schedule is registered by this function."""
    return Schedule(
        action=ScheduleActionStartWorkflow(
            PolicyFreshness.run,
            "synthetic-kora-1",
            id="relay-policy-check",
            task_queue="relay-reference",
        ),
        spec=ScheduleSpec(
            calendars=[ScheduleCalendarSpec(hour=[ScheduleRange(9)])], time_zone_name="Africa/Lagos"
        ),
        policy=SchedulePolicy(
            overlap=ScheduleOverlapPolicy.SKIP,
            catchup_window=timedelta(hours=1),
            pause_on_failure=True,
        ),
    )
