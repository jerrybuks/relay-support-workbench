"""Actual read-only remote MCP lookup; no local/global Codex configuration changes."""

import asyncio
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    report = {"mode": "live-remote-MCP", "server": "https://developers.openai.com/mcp"}
    async with streamable_http_client(report["server"]) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            operations = await session.list_tools()
            report["tools"] = [tool.name for tool in operations.tools]
            search = next(t for t in operations.tools if "search" in t.name.lower())
            fields = search.input_schema.get("properties", {})
            args = {}
            for name in search.input_schema.get("required", []):
                args[name] = (
                    "embeddings dimensions text-embedding-3-small" if name in {"query", "q"} else ""
                )
            if "query" in fields:
                args["query"] = "embeddings dimensions text-embedding-3-small"
            result = await session.call_tool(search.name, args)
            if result.is_error:
                raise RuntimeError("Remote documentation search failed")
            texts = [item.text for item in result.content if getattr(item, "type", "") == "text"]
            report.update(
                tool=search.name, arguments=args, result="\n".join(texts), status="passed"
            )
    path = Path("workbench/.runtime/contact2/evidence/mcp.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "result"}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
