"""Read-only local MCP fixture. No Linear/GitHub connection or write tool."""

from mcp.server import MCPServer

TICKET = {
    "id": "RELAY-17",
    "title": "Repeated completion event records duplicate service credits",
    "description": "Re-deliver the same event twice. The isolated before fixture records ₦4,000 "
    "instead of ₦2,000. Fix idempotency without weakening approval checks.",
    "acceptance": [
        "One effect per event ID",
        "Conflicting payload rejected",
        "Regression test",
        "Baseline service authorization remains intact",
    ],
    "mode": "local-fixture",
}

server = MCPServer("relay-fixture-tickets")


@server.tool()
def get_ticket(ticket_id: str) -> dict:
    """Read the single allowlisted workshop ticket; no external request or mutation."""
    if ticket_id != TICKET["id"]:
        raise ValueError("Ticket outside this fixture's allowlist")
    return TICKET.copy()


if __name__ == "__main__":
    server.run(transport="stdio")
