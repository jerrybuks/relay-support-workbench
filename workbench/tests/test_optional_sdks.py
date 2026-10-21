import asyncio

import pytest


def test_mcp_real_protocol_allowlist():
    pytest.importorskip("mcp", reason="Install the references extra to verify the actual MCP SDK")
    from mcp import Client

    from teaching.mcp_reference import server

    async def run():
        async with Client(server) as client:
            result = await client.call_tool("get_ticket", {"ticket_id": "RELAY-17"})
            assert not result.is_error
            assert "local-fixture" in str(result)
            denied = await client.call_tool("get_ticket", {"ticket_id": "PRIVATE"})
            assert denied.is_error

    asyncio.run(run())


def test_langchain_and_langgraph_components():
    pytest.importorskip("langgraph", reason="Install references extra for graph verification")
    from teaching.component_reference import build_review_graph

    result = build_review_graph().invoke(
        {"text": "Review policy evidence. " * 30, "chunks": [], "state": "new"}
    )
    assert result["state"] == "awaiting_human_review"
    assert len(result["chunks"]) > 1
    assert max(len(chunk) for chunk in result["chunks"]) <= 180


def test_schedule_definition_is_bounded_and_does_not_register():
    pytest.importorskip("temporalio", reason="Install references extra for schedule verification")
    from temporalio.client import ScheduleOverlapPolicy

    from teaching.temporal_reference import freshness_schedule

    schedule = freshness_schedule()
    assert schedule.spec.time_zone_name == "Africa/Lagos"
    assert schedule.policy.overlap == ScheduleOverlapPolicy.SKIP
    assert schedule.policy.pause_on_failure
