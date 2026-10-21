"""Opt-in actual Temporal server/worker integration, separate from SDK/unit checks."""

import asyncio
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.skipif(
    os.getenv("RELAY_TEMPORAL_TEST") != "1",
    reason="Opt-in Temporal test-server download/process required",
)
def test_temporal_worker_restart_and_duplicate_signal(tmp_path):
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    from teaching.temporal_reference import CreditApproval, record_credit

    async def run():
        async with await WorkflowEnvironment.start_time_skipping(
            download_dest_dir=str(tmp_path)
        ) as env:
            proposal = {
                "id": "PR-TEST",
                "amount_naira": 2000,
                "ledger_path": str(tmp_path / "effects.sqlite"),
            }
            with ThreadPoolExecutor(max_workers=2) as executor:

                def worker():
                    return Worker(
                        env.client,
                        task_queue="relay-test",
                        workflows=[CreditApproval],
                        activities=[record_credit],
                        activity_executor=executor,
                        max_cached_workflows=0,
                    )

                async with worker():
                    handle = await env.client.start_workflow(
                        CreditApproval.run,
                        proposal,
                        id="relay-restart-test",
                        task_queue="relay-test",
                    )
                    assert await handle.query(CreditApproval.status) == "awaiting_review"
                # No worker is active here. The signal and run state live in the server.
                decision = {
                    "proposal_id": proposal["id"],
                    "role": "supervisor",
                    "decision": "approve",
                }
                await handle.signal(CreditApproval.review_proposal, decision)
                await handle.signal(CreditApproval.review_proposal, decision)
                async with worker():
                    result = await handle.result()
                    assert result["status"] == "recorded-local-only"
            with sqlite3.connect(proposal["ledger_path"]) as db:
                assert db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1

    asyncio.run(run())


@pytest.mark.skipif(
    os.getenv("RELAY_TEMPORAL_TEST") != "1",
    reason="Opt-in Temporal dev-server download/process required",
)
def test_real_schedule_trigger_pause_and_delete(tmp_path):
    from temporalio.worker import Worker

    from teaching.temporal_dev import local_service
    from teaching.temporal_reference import PolicyFreshness, freshness_schedule

    async def run():
        async with local_service(tmp_path) as client:
            async with Worker(client, task_queue="relay-reference", workflows=[PolicyFreshness]):
                handle = await client.create_schedule(
                    "relay-fixture-schedule", freshness_schedule()
                )
                try:
                    await handle.trigger()
                    for _ in range(100):
                        description = await handle.describe()
                        if description.info.recent_actions:
                            break
                        await asyncio.sleep(0.1)
                    assert description.info.recent_actions
                    action = description.info.recent_actions[-1].action
                    result = await client.get_workflow_handle(action.workflow_id).result()
                    assert result["mode"] == "local-fixture"
                    assert result["status"] == "review_required"
                    await handle.pause(note="Workshop test complete")
                    assert (await handle.describe()).schedule.state.paused
                finally:
                    await handle.delete()

    asyncio.run(run())
