# Contact 3 — Codex across the SDLC with Shoplytic

**Format:** 60 minutes: 15 minutes of slides, 45 minutes of guided demonstration. Audience: a new engineer joining Shoplytic. One small change connects research, planning, implementation, tests, review and release preparation.

**Deliverables:** [presentation](../../workbench/src/relay/static/contact3.html), this facilitator guide, and a printable deck exported to `workbench/.runtime/browser-evidence/contact-3-shoplytic.pdf`. Open the presentation through Relay at `/static/contact3.html`; arrow keys move slides and the on-screen controls expose notes and printing.

**How I use this handbook:** The quoted passages are words I can say directly to the class. The prompts are ready to paste into Codex. The tables and checks are my preparation notes. Every slide speaker note is written as my explanation to learners, using “I” and “we.” The extra connection slide is an optional reference, so the timed session remains 60 minutes.

**Preparation status:** This guide is based on source inspection on 26 October 2026. A [completed, runnable MCP reference](../../workbench/teaching/contact3_shoplytic/README.md) is now available in Relay's opt-in teaching folder, using a fixed snapshot of Shoplytic's golden dataset. Run `pnpm contact3:mcp:demo` for actual stdio discovery and calls, or `pnpm contact3:mcp:test` for its regression checks. The original Shoplytic repositories remain unchanged. No Shoplytic model calls, database operations, uploads, account configuration or deployment were performed. Local MCP results are fixture execution, not chatbot evaluation.

This Shoplytic session replaces the main Contact 3 demonstration for this delivery. The existing Relay ingestion, Temporal and scheduling exercises remain alternative material; do not add them to this hour.

## The story and the task

“You have joined the team. Before changing the shopping assistant, understand it and give engineers a safe way to inspect its evaluation examples from Codex.”

Build a standalone, read-only **stdio MCP server** exposing one tool:

```text
list_golden_cases(category: str | None = None) -> list[case]
```

It reads the fixed repository fixture `data/golden_data/test_cases.json`. Each returned case preserves all six fields: `id`, `category`, `query`, `expected_agent`, `expected_behavior`, `min_quality_score`. Omitted category returns all 15 current cases; a known category returns exact matches in source order; an unknown category returns `[]`. No caller-supplied file paths, app imports, database access, HTTP requests, model calls or mutation tools.

Why this task: it introduces MCP using an existing artifact, is useful to an onboarding engineer, runs without the ecommerce stack, and has an objective acceptance test. Reading golden cases is not running evaluations or demonstrating chatbot quality.

## My opening explanation

> Today, we’re joining Shoplytic as new engineers. I’ll use Codex to understand the code, plan a small change, build it, test it, review it and prepare a release. Along the way, we’ll separate what the source code does from what the documentation says it does.
>
> Our task is a read-only MCP server that exposes Shoplytic’s evaluation examples. I’ve prepared a working reference so we can see the end product and have a fallback for the live exercise.
>
> Codex can already read a local JSON file, so MCP adds limited value for this file alone. We’re using a small file to learn the interface. The stronger use is when a shared service owns the information or several clients need the same capability. MCP gives those clients a common way to discover and call it.

## My quick start and completed reference

I run these commands from the Relay repository root:

```sh
# Start the slides, if Relay is not already running.
pnpm dev

# In another terminal: print actual MCP discovery and tool responses.
pnpm contact3:mcp:demo

# Run the reference's 20 regression and protocol tests.
pnpm contact3:mcp:test
```

I open the slides at `http://127.0.0.1:8000/static/contact3.html`. I press **N** for my speaking notes, **G** for contents and **F** for fullscreen.

The completed code is in `workbench/teaching/contact3_shoplytic/`:

| File                   | What I show                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| `golden_cases.py:31`   | An ordinary Python function that reads, validates and filters one fixed fixture.                      |
| `server.py:15`         | `MCPServer(...)` creates the server object with its name and instructions.                            |
| `server.py:23`         | `mcp.tool(...)(list_golden_cases)` registers that function as a tool.                                 |
| `server.py:34`         | `mcp.run(transport="stdio")` starts serving MCP messages.                                             |
| `smoke.py`             | A real client launches a child process, initializes MCP, discovers the tool and checks calls.         |
| `data/test_cases.json` | A documented snapshot of Shoplytic's 15 cases; it does not track future source changes automatically. |

The reference tests are at `workbench/tests/test_contact3_mcp.py`, relative to the Relay root.

> The SDK handles the protocol messages, tool schema and argument validation. We still own the function's behavior, its access boundaries and its tests. The read-only annotation describes the tool; the implementation makes it read-only.

The planned learner patch uses `tools/` inside a disposable Shoplytic backend checkout. The completed reference uses Relay's opt-in teaching folder instead. I make that path difference explicit before copying commands. I can inspect the completed reference without creating another checkout; the live implementation exercise uses a disposable checkout so we can watch a fresh change.

## My MCP connection explanation

> When I say “our Python server,” I mean the MCP server we built. Shoplytic's FastAPI application is a different process and isn't needed for this exercise.
>
> MCP Inspector is an existing npm package, `@modelcontextprotocol/inspector`. I didn't build its interface. It is a test client that discovers tools, builds an argument form, sends calls and shows results and protocol messages.

```text
Browser Inspector UI
    → local HTTP → Inspector's Node.js backend
    → MCP over stdin/stdout → our Python MCP server
    → fixed JSON fixture

Results return along the same path.
```

> When I switch the connection toggle on, the browser asks Inspector's backend to connect. The backend has our Python command and server path. It launches the Python file, which reaches `mcp.run(transport="stdio")` and waits for MCP messages. Inspector initializes the connection and asks which tools are available.
>
> When I click Execute Tool, Inspector sends the tool name and arguments over those input/output streams. Our function reads and filters the fixture, and the result comes back to the browser. The Python stdio server has no web address of its own; the address I open belongs to Inspector.
>
> No model is connected in this manual test. To use the tool from Codex, we would separately configure Codex with the same Python launcher. Its host would then make the tool available to its model. Inspector's toggle only connects Inspector; it doesn't connect Codex or a model.

### My Inspector walkthrough

If the current Inspector is still running, I open `http://127.0.0.1:6274`. Otherwise, with **Node 22.19+** active, I run this from the Relay root in another terminal:

```sh
npx --yes @modelcontextprotocol/inspector@2.12.0 workbench/.venv/bin/python workbench/teaching/contact3_shoplytic/server.py
```

I open the local URL printed by the command. On this machine, Inspector was launched using the installed Node 24 runtime. If my shell still uses Node 22.16, I select the installed Node 24 runtime before launching it. I keep the generated Inspector session token local.

1. I enable the server's connection switch and wait for **Connected**.
2. I open **Tools**, then **List Shoplytic golden cases**.
3. I enter `product_search` under **Category** and click **Execute Tool**.
4. I show the three returned cases and the structured response, `{"result": [...]}`.
5. I open the **Protocol** panel and point out initialization, discovery and the tool call. I can repeat the call with an unknown category to show an empty result.

| Input                          | What I expect                                                               |
| ------------------------------ | --------------------------------------------------------------------------- |
| Omitted category or `null`     | 15 cases                                                                    |
| `product_search`               | 3 cases                                                                     |
| Unknown category               | Empty list                                                                  |
| Numeric category, such as `42` | Argument error; I show this through the smoke test or JSON argument editor. |

If connection fails, I check the Python executable, absolute script path and installed reference dependencies. I keep diagnostics off stdout. If the browser UI is unavailable, I use `pnpm contact3:mcp:demo` as a separate real protocol check; I label it as a terminal demonstration. The observed local evidence is saved at `workbench/.runtime/contact3/mcp-smoke.json`. I don't present a recording or a direct function call as a live browser test.

### My boundary for the deployment segment

> We'll finish with release preparation and rollback instructions. We are not deploying the ecommerce application to the cloud in this hour. The MCP tool runs locally over stdio. Deploying the storefront and API would need a separately scoped staging and promotion task.

## My preparation before learners arrive

1. I open both repositories read-only: `../shoplytic/agentic-ecommerce` and `../shoplytic/agentic-ecommerce-fe`. Check their current commit IDs and working tree status. The audited backend commit was `bfd79b4`; reassess source claims if it differs.
2. I prepare a disposable writable clone or checkout of the backend, outside the owner's working copy. Run the exercise there. Preserve the original fixture and application configuration.
3. I verify the available Python version and the current MCP Python SDK API in the [official SDK documentation](https://py.sdk.modelcontextprotocol.io/). Select and record one compatible SDK version; install it in an isolated demo virtual environment. Do not install the full ecommerce application merely to read JSON. The checked-in backend does not already declare this proposed MCP dependency.
4. I rehearse the stdio client/server smoke test with the selected SDK. Keep diagnostics on stderr; stdout belongs to MCP. Confirm your Codex client supports MCP and subagents. Do not assume account features or connectors are configured.
5. I prepare a clearly labeled recording or terminal transcript of the same task as fallback. If SDK installation or protocol setup fails during class, explain the blocker and use that evidence; do not call a pure loader test an MCP integration pass.
6. I keep an editor, terminal and the slide deck ready. No API keys, database or live Shoplytic app is needed for the core exercise. Do not start `src.main`: importing it creates tables and initializes vector stores.

The optional connection from Codex to the prepared local server changes client configuration. Demonstrate it only in a disposable classroom profile explicitly selected for the exercise; otherwise show the reviewed launch command and protocol transcript. Preparing this guide does not authorize changes to an actual account or deployment.

## Run of show

| Time  | Activity                                                                   | Visible evidence                                                    |
| ----- | -------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 0–15  | Slides: onboarding story, architecture, context, MCP, evaluations, release | One request-flow diagram and one task contract                      |
| 15–23 | Research with two read-only Codex subagents                                | Concise summaries with file/line references                         |
| 23–28 | Plan the MCP slice                                                         | Files, acceptance checks, exclusions                                |
| 28–38 | Implement in the disposable backend checkout                               | Small reviewable diff                                               |
| 38–46 | Test loader and real MCP protocol                                          | Offline assertions; `tools/list` and `tools/call` results           |
| 46–53 | Fresh independent review and repair                                        | Findings, targeted fix, rerun evidence                              |
| 53–60 | Stage the local release and explain rollback                               | Exact launch command, version/evidence record, rollback instruction |

If time slips, shorten the architecture discussion and use a labeled prepared diff. Keep the test and independent review stages.

## 1. Research: follow one request

Paths below are relative to the relevant Shoplytic repository, not Relay.

| Layer              | Open this file                                          | What to explain                                                                                                                                   |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| UI                 | frontend `src/components/Chatbot.tsx:173`               | Sends chat and refreshes cart queries when the order agent was used. Loading text is timer-driven, not streamed execution evidence.               |
| API client         | frontend `src/services/api.ts:85`                       | POSTs the query; backend base URL is currently hardcoded at line 3.                                                                               |
| HTTP contract      | backend `src/routes/user.py:71` and `:101`              | Validates input, establishes session, invokes service and returns sources, agent names, routing and timing.                                       |
| Service            | `src/querying/service.py:23`                            | Holds conversation memory and the orchestrator.                                                                                                   |
| Routing            | `src/querying/agents/orchestrator.py:44`                | Two specialist routing functions: general information and orders. Different specialists may run with `asyncio.gather` at line 246.                |
| Policy specialist  | `src/querying/agents/general_info.py:60`                | Directly retrieves handbook context before generating an answer.                                                                                  |
| Order specialist   | `src/querying/agents/order.py:42` and `:289`            | Exposes bounded tools and limits the tool loop to six steps.                                                                                      |
| Retrieval          | `src/querying/tools/retrieval.py:197`                   | Filters product metadata, applies similarity and price checks, and retains product IDs.                                                           |
| Source preparation | `src/build_index.py:37`                                 | Parse products/handbook, chunk, embed, store in separate Chroma collections. Rebuilding clears the existing index: do not run against owner data. |
| Business state     | `src/querying/tools/order.py:699`                       | Voucher validation and transaction commit/rollback; separate from the model's prose.                                                              |
| Memory             | `src/utils/memory.py:29` and `:80`                      | Last ten exchanges per session; carries product identifiers into follow-up context.                                                               |
| Quality            | `src/utils/evaluation.py:15`; `tests/test_runner.py:86` | Runtime judge and golden runner measure different things.                                                                                         |

I explain: “Shoplytic's agents help shoppers. Codex's subagents help us engineer Shoplytic.” Shoplytic uses custom Python orchestration and OpenAI-compatible Chat Completions. It is not an MCP implementation or a durable workflow engine.

### My first prompt: learn what I have joined

> I don’t know the internal architecture yet. I’ll describe what I need to learn, and ask Codex to discover the structure from the repositories. The code map above is my preparation reference, not information I need to put in my first prompt.

```text
I’ve just joined Shoplytic and haven’t worked with these repositories before.
The repositories are ../shoplytic/agentic-ecommerce
and ../shoplytic/agentic-ecommerce-fe.
Please read the project guidance, READMEs and source, then explain what the
product does, what each repository is responsible for, and where I should
start reading. Walk me through one main user journey and tell me how the
project is run and checked, based on what you find.
Keep it understandable for a new teammate. Link important claims to files,
and flag anything the code doesn’t establish. Read only for now; don’t
change files, read credentials or start services.
```

The only project-specific context I supply is the two repository paths. I don’t name an orchestrator, golden data or a judge before discovering them. If a README and the code disagree, I ask to see the source before drawing a conclusion.

### My second prompt: delegate after the first overview

```text
Now use two read-only subagents to investigate independently.
Have one follow the user journey you identified through the relevant code.
Have the other inspect how the team checks quality and prepares releases.
Let each choose the relevant files from what is actually present.
Bring back a short explanation with file references, open questions and
anything I should verify before making my first change. Don’t change files
or run services, external calls or tests that could change application data.
```

> I’m splitting independent questions, not giving two agents the same job. Their findings help me decide where to look next. I’ll keep the short synthesis and references in the main thread, rather than copying all their working context.

### My third prompt: draw what we learned

```text
Based only on the code we just inspected, draw a simple architecture diagram
for a new teammate. Show the main components and how one user request moves
between them. Use about 8–10 boxes and plain labels. Keep background work
separate from the request path. Explain each arrow briefly and give source
references below the diagram. Mark uncertainties; don’t add components or
connections just because a typical application might have them.
Use an available sketch/diagram tool, or Mermaid if none is available.
Don’t change application code.
```

> Before I move on, I’ll use the picture to explain the system back to you. If I can’t explain an arrow, we’ll inspect that connection in the code.

Using `/sketch` here makes sense **if it is available in the client I’m presenting from**. I type `/` and check the available commands rather than promising a command that isn’t available. The current official command references do not establish `/sketch` as a standard command. The same request works in plain language; Mermaid is the fallback. I assess the diagram by its source-backed relationships, not its appearance. I keep the shopping application diagram separate from the engineering MCP connection diagram.

My budget within 15–23 minutes: about two minutes for the first overview, three for delegated findings, two for the diagram and one to verify a finding. If research takes longer, I use a labeled prepared code map and preserve time for the build, tests and review.

### My follow-up when the quality system is discovered

I use this only after the findings identify evaluation files, or as a deeper reference outside the eight-minute onboarding segment:

```text
You found evaluation examples and response scoring. Show me one example
and follow how the code uses it. What actually makes a check pass or fail?
Explain what the model-based scoring sees, what it cannot verify, and what
we would still need to check ourselves. Use the current code as evidence;
don’t run the chatbot or make model calls.
```

I ask everyone to follow one line reference themselves. The agent’s summary and diagram are navigation aids, not proof without the source.

## 2. Plan: make the acceptance contract explicit

I now introduce an explicit **workshop ticket**. I don’t pretend the onboarding agent independently discovered a business need for MCP.

> Our workshop ticket is to make the existing evaluation examples accessible through a read-only MCP tool. This is an assigned learning task. We’ll discuss its limited value for a local file and the stronger shared-service use case before we plan it.

```text
My first workshop ticket is to let engineers and assistants inspect the
existing evaluation examples through a read-only MCP tool, without running
the shopping application or its evaluations.
In this disposable backend checkout, propose the smallest implementation.
Use the dataset we found. Suggest the tool’s inputs, returned fields,
filtering behavior, errors, files to change and meaningful tests.
Keep it a local stdio server with no data writes or caller-supplied paths.
Use the MCP SDK version verified for our demo; check the matching API docs.
Keep the application behavior and original dataset unchanged.
Explain the plan and what done means before editing anything.
```

I check the proposed contract against the prepared reference: `list_golden_cases(category=None)`, all six case fields, source order, exact category filtering and `[]` for unknown categories. These details enter our context through research and planning, rather than the first onboarding prompt. I review for five outcomes: complete fields; deterministic filtering; launch from another directory; no ecommerce dependencies or side effects; real MCP schema/call evidence. Pin the MCP SDK version used in rehearsal. There is no need to build a new agent framework, dashboard, REST endpoint or hosted MCP service.

## 3. Execute: one writer and a bounded diff

```text
Implement the plan we agreed on in this disposable checkout.
Keep one agent responsible for edits and stay within the agreed files.
Keep the data-loading code separate from the MCP adapter. Don’t change
application behavior, run the commerce backend or modify the source data.
Run the agreed checks that are safe to run locally. Show me the diff,
exact launch command, checks performed and anything still unfinished.
```

I keep implementation in the main agent; research and review can use independent contexts. Multiple agents editing the same files add coordination work without helping this small slice.

### Context that survives a handoff

I explain the difference between persistent instructions and transient task state:

| Mechanism            | Job in this exercise                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `AGENTS.md`          | Short repository rules: commands, boundaries, safe data handling. Instructions do not create permissions.            |
| Skill                | A reusable procedure, such as the team's review process. Invoke an applicable installed skill; do not fabricate one. |
| MCP                  | A protocol exposing a tool and its input/output contract. Availability of a tool does not authorize every use.       |
| Specialized subagent | A delegated role with a narrow question, scope and expected return. It consumes its own context and tokens.          |
| Task handoff         | Current decision, files, evidence and next action needed to resume this specific change.                             |

This is the handoff I paste into a fresh implementation/review context:

```text
Goal: read-only stdio list_golden_cases MCP tool in disposable backend clone.
Contract: fixed golden JSON; six fields; all cases or exact category;
unknown => []; preserve order; no path input, src imports or network.
Allowed files: tools/golden_cases.py, tools/golden_cases_mcp.py,
tests/test_golden_cases.py, minimal optional deps/docs.
Source: data/golden_data/test_cases.json has 15 cases on audited commit.
SDK/version: [record the version actually installed].
State: [record changed files and current diff].
Evidence: [paste exact commands/results, or say not run].
Next: protocol smoke test, fresh review, then local release preparation.
```

I give subagents relevant file paths and the question, then request concise findings. Keep large source dumps and full traces out of the parent context; retain decisions and references.

## 4. Test: prove the contract before judging prose

```text
Check the implementation against our agreed acceptance criteria.
Use disposable inputs to test normal results, category filtering, unknown
categories, invalid arguments and missing or malformed data. Check that
launching from another working directory still finds the fixed dataset.
Then use a real MCP client over stdio to discover and call the tool.
Show the schema, actual results and errors; a direct function call alone
isn’t enough. Confirm the dataset stayed unchanged and clean up processes.
Don’t run the shopping API, database operations or model-backed evaluations.
Report exact commands and observed results, including checks you couldn’t run.
```

The existing `python -m tests.test_runner` is **not** this offline test. It posts shopping queries to an API, including cart/shipping actions, and can incur model/judge calls. Do not run it against a shared or owner deployment for this exercise.

### What the golden data and LLM judge really do

The fixture contains 15 examples in nine categories. Its six fields express the query, routing expectation, desired behavior and quality threshold. It is a starting regression set, not training data or proof of coverage.

The current runner (`tests/test_runner.py:86`) marks success from agent matching. It does **not** enforce `expected_behavior` or `min_quality_score`, inspect final database state, or await judge scores. Its generated test session is sent to an endpoint that derives identity from IP instead.

The runtime judge (`src/utils/evaluation.py:15`) scores relevance, accuracy, completeness, clarity and helpfulness, plus overall quality. `orchestrator.py:352` schedules it in the background and attaches scores to Langfuse when a trace ID exists. It sees query, response and agent names; it does not receive retrieved evidence, golden expectations or database state. Missing scores default to 5 in parts of the implementation. A high score cannot prove factual grounding, a cart mutation or a safe purchase.

I show one concrete mismatch: `voucher_001` expects generating a $100 voucher, while the user voucher endpoint describes a fixed $2000 voucher and the order agent exposes no voucher-generation tool. Golden expectations need human maintenance too.

Improvement discussion, not extra build work: deterministic state assertions first, judge grounded responses with supporting evidence second, calibrate against human labels, add negative/isolation cases, and distinguish failed/missing evaluation from a passing score.

## 5. Review: use a fresh independent reader

```text
Use a fresh read-only reviewer subagent that didn’t implement the change.
Give it our task, agreed acceptance criteria, actual diff and test results.
Ask it to look for correctness issues, unintended data access or writes,
protocol problems and missing tests. Findings should include file references
and explain the impact. It should flag unverified claims and not edit files.
Summarize what needs fixing before we release the tool locally.
```

I use the main agent to triage findings, make the smallest justified repairs and rerun affected checks. A second model opinion is useful; acceptance remains tied to source and executable evidence.

If the review finds a problem, I use this repair prompt before returning to release preparation:

```text
Check the reviewer’s findings against the code. Fix the confirmed issues
within our existing scope, explain any finding you disagree with, and rerun
the affected checks. Show the updated diff and actual results. Don’t expand
this into unrelated application fixes.
```

I use these existing patterns to keep our discussion balanced:

| Useful pattern in Shoplytic           | Practical limit to explain                                                                                                                      |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Separate routing and specialist tools | Sequential specialist execution does not feed one specialist's output into the next (`orchestrator.py:269`).                                    |
| Purchase gates and DB transaction     | Existing voucher check is partial idempotency; empty-cart checks happen first and concurrency safety is not established (`tools/order.py:680`). |
| Bounded per-session history           | Sessions are IP-derived; shared Wi-Fi can share history/cart. Memory and carts are process-local (`routes/user.py:54`, `utils/cart.py:28`).     |
| Traces and asynchronous judge         | Background judgment may be missing; it is not a release gate or correctness proof.                                                              |
| Explicit specialist prompts           | “Exactly one tool” is a prompt rule; the executor loops over returned tool calls (`order.py:348`).                                              |

I keep these as an onboarding backlog. We use them to discuss scope rather than starting five extra fixes during the hour.

## 6. Release: prepare a local tool, then explain app deployment

```text
Prepare a local release handoff for the tool we built.
Include the source version, Python and SDK versions, exact launch command,
observed test evidence, known limits, and how to stop or roll it back.
Explain what I would enter in an MCP client and how to verify the connection.
Keep client registration separate from running Inspector. Don’t change real
account settings, commit, publish or deploy anything.
Also inspect what these repositories establish about deploying the original
web application. Explain the available commands, missing setup, staging
checks and rollback questions. Distinguish evidence from assumptions.
```

For the local release, the MCP client starts a stdio subprocess. It does not need a public URL, Render or Vercel. Demonstrate launch and protocol evidence in the isolated environment. Client registration, if explicitly authorized in a disposable profile, is separate from publishing a server.

For the ecommerce application, frontend `vercel.json` contains an SPA rewrite and the README links Render/Vercel deployments. Those are hosting clues, not verified deployment success. The inspected backend has no host deployment configuration, and no CI pipeline was verified. HEAD `/health` (`src/main.py:87`) returns a constant rather than checking dependencies.

An application release would need a separate approved task: establish commands/configuration, stage secrets, provision isolated data, build/index deliberately, smoke-test the staged UI/API and confirm rollback. The frontend's hardcoded API base URL is a useful future issue: configure it per environment before claiming staging isolation. Do not silently repoint it or deploy the unreviewed onboarding backlog.

I close by checking the evidence we have seen: a code map, a small acceptance contract, a bounded diff, offline and protocol checks, independent findings, and a launch/rollback record. If any stage used a recording or was only described, label it.

## My prompt checklist

I use these in order; later prompts rely on findings and decisions from earlier steps.

| Stage                      | Prompt supplied here                         | What I bring forward                                                   |
| -------------------------- | -------------------------------------------- | ---------------------------------------------------------------------- |
| Discover                   | First onboarding prompt                      | Product purpose, repository responsibilities, entrypoints and unknowns |
| Investigate                | Two independent read-only subagents          | Source-backed journey and quality/release findings                     |
| Understand                 | Architecture sketch request                  | Verified component relationships; no invented connections              |
| Inspect quality, if needed | One-example follow-up                        | What checks and model scores actually establish                        |
| Scope and plan             | Explicit workshop ticket                     | Agreed tool contract, files and acceptance criteria                    |
| Execute                    | Implement the agreed plan                    | Focused diff and recorded checks                                       |
| Test                       | Behavior plus real MCP protocol              | Observed results and errors                                            |
| Review and repair          | Fresh reviewer plus repair prompt            | Confirmed findings, repairs and targeted reruns                        |
| Handoff                    | Context handoff template                     | Decisions, version, paths, evidence and next action                    |
| Release                    | Local launch and deployment-readiness prompt | Reproducible launcher, recovery steps and separate hosting questions   |

I don't paste the whole checklist into the first message. I let the conversation gain detail as we learn. The prompt blocks are copyable; the surrounding source map and expected results are my facilitator notes.

## Sources and further reading

- [Desktop slash commands](https://learn.chatgpt.com/docs/reference/slash-commands): check the actual client command list; `/sketch` is optional and not established by this reference.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): delegation and specialized agent configuration.
- [Codex customization](https://learn.chatgpt.com/docs/customization/overview): project instructions, skills, MCP and agents.
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp): client connection guidance; verify against the client used for class.
- [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/): authoritative SDK API and transport examples.
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector): the existing testing client and its browser interface.

Repository descriptions above come from read-only source inspection, not the earlier project's report or README claims of live success.
