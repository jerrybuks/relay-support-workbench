# Shoplytic golden-case MCP server

Completed Contact 3 reference: one read-only tool, `list_golden_cases(category=None)`.
It reads a fixed teaching snapshot, returns all six fields in source order, and
filters by exact category. Unknown categories return an empty list. It never
imports the ecommerce application, executes shopping actions or calls a model.

The server uses the repository's locked **MCP Python SDK 2.3.0** and Python 3.12+.
It is opt-in teaching material and is excluded from Relay's baseline package.

From the Relay repository root:

```sh
# Install the existing locked reference dependencies if needed.
uv sync --project workbench --locked --extra references

# Test through a real stdio client and print a product-search response.
pnpm contact3:mcp:demo

# Unit tests, malformed input checks and a subprocess protocol smoke.
pnpm contact3:mcp:test

# Launch for an MCP host. It waits for MCP messages, not browser HTTP requests.
pnpm contact3:mcp
```

The demo prints observed results and writes the full discovery schema and tool
responses to `workbench/.runtime/contact3/mcp-smoke.json`. This is local MCP
execution against a fixture, not an LLM evaluation or a production integration.

## What to try

| Arguments                        | Result                     |
| -------------------------------- | -------------------------- |
| `{}` or `{"category": null}`     | All 15 cases               |
| `{"category": "product_search"}` | Three product-search cases |
| `{"category": "general_info"}`   | Three policy cases         |
| `{"category": "missing"}`        | `[]`                       |
| `{"category": 42}`               | Tool argument error        |

The structured MCP response wraps the list as `{"result": [...]}`. No file path
argument or mutation tool is exposed. Read-only annotations describe behavior;
the fixed loader and its lack of mutation operations implement that behavior.

## Browser Inspector

With Node 22.19+ active, launch the official Inspector from the repository root:

```sh
npx --yes @modelcontextprotocol/inspector@2.12.0 workbench/.venv/bin/python workbench/teaching/contact3_shoplytic/server.py
```

Open the local URL printed by the Inspector. Connect the stdio server, select
**Tools**, select `list_golden_cases`, enter `product_search` for `category` and
run the tool. Inspect the three returned cases and the protocol messages.
The browser belongs to the Inspector; the MCP server itself remains a stdio
process. Close the Inspector to stop this demo connection.

For a host that asks for command and arguments, use absolute paths:

```text
Command: /Users/jerrychibuokem/projects/history-game-codex/workbench/.venv/bin/python
Arguments: /Users/jerrychibuokem/projects/history-game-codex/workbench/teaching/contact3_shoplytic/server.py
Transport: stdio
```

This launcher works from other working directories. A host starts and stops the
child process; the stdio server has no web URL. The separate official MCP
Inspector can provide a browser interface. Existing Codex/account configuration
is not changed by running these scripts.

## Fixture provenance

`data/test_cases.json` is a byte-for-byte snapshot of
`shoplytic/agentic-ecommerce/data/golden_data/test_cases.json`, backend commit
`bfd79b4`, copied on 26 October 2026.

SHA-256: `a93a62d1b90b478fa0738cc36452178743537a13d01f99d31fbb31bcfd9be7cc`.

The original sibling repositories remain unchanged. The snapshot does not
automatically track future edits. Case queries and expected behavior are
untrusted data to inspect, never instructions to execute.

See the [facilitator guide](../../../docs/teaching/CONTACT_3_SHOPLYTIC.md) for the
SDLC demonstration and [official SDK docs](https://py.sdk.modelcontextprotocol.io/)
for the MCP implementation APIs.
