"""A real stdio MCP client: discover, call, validate and print observed evidence."""

import asyncio
import hashlib
import json
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mcp import Client, StdioServerParameters

from teaching.contact3_shoplytic.golden_cases import DATA_PATH, list_golden_cases

SERVER_PATH = Path(__file__).resolve().with_name("server.py")


async def run_smoke(cwd: Path) -> dict:
    """Use a subprocess, not an in-memory server or direct tool invocation."""
    before = DATA_PATH.read_bytes()
    report = {
        "mode": "local-stdio-MCP / checked-in fixture / no LLM calls",
        "python": sys.version.split()[0],
        "mcp_sdk": version("mcp"),
        "fixture_sha256": hashlib.sha256(before).hexdigest(),
        "calls": [],
    }
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=cwd,
        env={"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    async with asyncio.timeout(30):
        # Legacy negotiation deliberately exercises initialize + tools/list + tools/call.
        async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
            report["server"] = client.server_info.model_dump()
            tools = (await client.list_tools()).tools
            assert [tool.name for tool in tools] == ["list_golden_cases"]
            tool = tools[0]
            assert set(tool.input_schema["properties"]) == {"category"}
            assert "category" not in tool.input_schema.get("required", [])
            assert tool.annotations.read_only_hint is True
            report["tool"] = tool.model_dump(mode="json", exclude_none=True)
            for args in (
                {},
                {"category": None},
                {"category": "product_search"},
                {"category": "missing"},
            ):
                result = await client.call_tool("list_golden_cases", args)
                assert not result.is_error, result
                actual = result.structured_content
                expected = list_golden_cases(args.get("category"))
                assert actual == {"result": expected}, actual
                report["calls"].append(
                    {"arguments": args, "count": len(expected), "structured_content": actual}
                )
            invalid = await client.call_tool("list_golden_cases", {"category": 42})
            assert invalid.is_error, "Invalid category was accepted"
            report["invalid_argument_rejected"] = True
            unknown = await client.call_tool("delete_golden_cases", {})
            assert unknown.is_error, "Unexpected mutation tool was accepted"
            report["unknown_tool_rejected"] = True
    assert DATA_PATH.read_bytes() == before, "Fixture changed during protocol smoke"
    report["fixture_unchanged"] = True
    report["status"] = "passed"
    return report


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="shoplytic-mcp-") as folder:
        report = await run_smoke(Path(folder))
    target = Path(__file__).resolve().parents[2] / ".runtime/contact3/mcp-smoke.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Connected to {report['server']['name']} using MCP SDK {report['mcp_sdk']}")
    print("Discovered: list_golden_cases(category: string | null = null)")
    for call in report["calls"]:
        print(f"  {json.dumps(call['arguments'])} -> {call['count']} cases")
    print("\nActual product_search result received over MCP:")
    print(json.dumps(report["calls"][2]["structured_content"], indent=2))
    print("\nPASS: invalid input rejected; unknown tool rejected; fixture unchanged")
    print(f"Evidence: {target}")


if __name__ == "__main__":
    asyncio.run(main())
