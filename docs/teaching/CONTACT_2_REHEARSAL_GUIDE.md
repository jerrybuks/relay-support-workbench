# Contact 2 rehearsal guide

Teach one task over 120 minutes: give Relay a new approved policy and prove that its answers use the right evidence. Follow the document through ingestion, then follow a question through retrieval and generation. Use Codex to implement the missing ingestion path with repository instructions, skills, scoped tools, tests and review.

**Status on 22 October 2026: technical preparation verified.** The reference ingestion pipeline, independent parser checks, real OpenRouter answers, MCP lookup, browser journeys, bounded Codex repair and read-only permission denial have recorded evidence. The live parser is intentionally unfinished. Your remaining task is the timed teaching rehearsal. Native Goal support is detected in the installed CLI; practise its lifecycle and the Plan-mode controls in your teaching client before delivery. No cloud/SDK execution or two-hour facilitator rehearsal is claimed.

This replaces the older 60-minute duplicate-event exercise as the main Contact 2 session. The duplicate-event fixtures remain optional practice. Contact 2 now has two hours; Contacts 1, 3 and 4 retain their existing allocations unless separately changed. With three other one-hour contacts, total facilitated time becomes five hours.

## Outcome and assignment

Read aloud:

> Kora Dispatch has approved a new parcel-collection policy. Support agents need Relay to answer questions about it and show where the answer came from. We will add that capability with Codex. We will follow the document into the vector store, follow the question back to its evidence, and verify the result before reviewing the change.

Use original synthetic policy text. Keep the same app, document, question and task visible throughout. The second document is a reuse check, not a separate project.

The exercise must finish with these observable results:

- An approved Markdown document with validated source ID, title, version, tenant and visibility can be ingested into a disposable teaching workspace and index.
- Ingestion previews coherent chunks and stores their source metadata with embeddings. Repeating unchanged ingestion reuses vectors without duplicating sources.
- The new source becomes available through the app's canonical document store as well as the vector index. Indexing a file alone is insufficient: retrieval checks chunks against authorized canonical documents.
- A question retrieves the expected permitted passage and produces an answer with a validated citation to its version.
- Missing metadata, conflicting IDs, unreviewed documents and restricted sources are handled by application rules. A document cannot grant itself approval through its prose.
- Existing case, role, tenant, approval and idempotency checks still pass. The diff and PR draft describe actual tests and remaining limitations.

Freeze the document text, expected answers and input format before rehearsal. The approved status is a synthetic teaching record; the exercise does not certify real business content.

## Start your rehearsal

The prepared class checkout is `~/projects/relay-contact2-class`. Open that folder in the IDE, not the normal project folder. Its `workbench/teaching/contact2/exercise.py` is the live edit; the original Relay app and Contact 1 runtime data stay separate.

The class app uses the single local port **8002**. Open:

- [Slides](http://127.0.0.1:8002/course/contact-2)
- [Policy lab](http://127.0.0.1:8002/teaching/contact-2)
- [Resolution desk](http://127.0.0.1:8002/dashboard)
- [Swagger](http://127.0.0.1:8002/docs)

The app is left in the **before** state. Previewing a policy returns the intentional `parser_not_implemented` error until you implement the parser. Asking the collection question before import should report insufficient evidence; a nonempty retrieval result alone does not prove support.

From the class checkout, rehearse the initial failing acceptance check:

```sh
workbench/.venv/bin/python workbench/scripts/contact2.py check --state before
```

Expected initially: exit 1. After the live edit: 16 independent checks pass with zero provider calls. The prepared reference check is:

```sh
workbench/.venv/bin/python workbench/scripts/contact2.py check --state reference
workbench/.venv/bin/python -m pytest workbench/tests/test_contact2_ingestion.py -q
```

Use the policy lab to preview and import. Preview makes no model request. Import requires a separate approval record, supervisor demo session and the billable-confirmation checkbox. The lab executes under the app's vector lock, so you do not need another server or a second index process.

If the server is stopped, run from the original project root:

```sh
uv run --project ~/projects/relay-contact2-class/workbench --locked --extra references --env-file workbench/.env python ~/projects/relay-contact2-class/workbench/scripts/contact2.py serve --state before --reload
```

Do not run a second server if port 8002 is occupied. The reloader picks up parser edits. For recovery, stop that server and use the same command with `--state reference` instead of `--state before --reload`. The reference parser uses the same app, UI and teaching database. Nothing resets automatically.

To launch Codex in the class checkout with the external documentation server available only for that invocation:

```sh
codex -C ~/projects/relay-contact2-class -c 'mcp_servers.openaiDeveloperDocs.url="https://developers.openai.com/mcp"'
```

Use the client model/effort controls, then Plan mode and the task prompt below. `/mcp` should list the documentation connection. For the prepared non-interactive example, inspect the recorded CLI events/result and actual repair patch at `workbench/teaching/contact2/artifacts/CODEX_REPAIR.patch`. The verification record includes real cached-token counts from Codex, separate from Relay's reported cached input.

The two general skills are installed under the class checkout's `.agents/skills`. The third skill reference is `workbench/teaching/contact2/skills/ingest-approved-policy/SKILL.md`; author it during the exercise, or copy it into `.agents/skills/ingest-approved-policy/` for recovery. Never install it globally for this class.

For a **fresh** additional checkout, run `pnpm contact2:setup --path ~/projects/relay-contact2-another` from the original repository. The setup refuses an existing destination. It installs locked dependencies and the two skills; it copies no credentials. A seed-only Contact 2 index can be reused without another API request. If a seed index cannot be reused, explicitly initialize the new teaching home with `contact2.py init --confirm-billable` before serving; never run it on Contact 1 data.

## Prepared assets and evidence

| Asset                      | Location and verification                                                                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Narrow live task           | `workbench/teaching/contact2/TASK.md`; implement the parser only                                                                                                   |
| Reference parser           | `workbench/teaching/contact2/parser_reference.py`; 16 independent offline acceptance checks                                                                        |
| Integration                | `workbench/teaching/contact2/pipeline.py`; canonical storage, matching review hash, index reuse and rollback tests                                                 |
| Policy fixtures            | `workbench/teaching/contact2/policies/`; two reusable team policies, one supervisor-only policy and three rejection examples                                       |
| Engineering skills         | `workbench/teaching/contact2/skills/`; all three pass skill validation; review skill exercised through Codex                                                       |
| External MCP               | `pnpm contact2:mcp`; actual remote tool discovery/search recorded                                                                                                  |
| Live preflight             | `pnpm contact2:preflight --confirm-billable`; disposable original synthetic data only                                                                              |
| Browser checks             | `pnpm contact2:browser`; `--ask` explicitly enables a real model request                                                                                           |
| Automation and permissions | `workbench/evidence/contact2-preparation.json`; actual CLI repair, corrective iteration, review and denied write                                                   |
| Slides                     | `/course/contact-2`; 22 slides, speaker notes, keyboard controls and AST-verified code references; printable PDF in `workbench/evidence/contact2-presentation.pdf` |
| Handover and PR draft      | `workbench/teaching/contact2/artifacts/`; fill with observed results before review                                                                                 |

Detailed local run logs, live answers, screenshots and MCP output are in ignored `workbench/.runtime/contact2/evidence/` in the original repository. The public evidence summary excludes credentials, session tokens and owner paths. It distinguishes provider, fixture and CLI results.

The installed CLI reports version 0.162.1, signed-in ChatGPT access and Goals enabled. Check the actual client controls during your rehearsal. We did not activate a persistent Goal in your current session or change global model/permission settings.

## Session timetable

| Minutes    | Activity                                                       | What learners must see                                                   |
| ---------- | -------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 0 to 10    | Establish the task and current evidence gap                    | One question, missing source, acceptance criteria                        |
| 10 to 35   | Trace ingestion and the answering path                         | Real functions with their actual inputs and outputs                      |
| 35 to 55   | Orient Codex controls and set up governed work                 | Prompt, `AGENTS.md`, skills, worktree, MCP and permissions               |
| 55 to 85   | Implement the bounded file-ingestion feature                   | Plan, failing acceptance check, patch, tests and data flow               |
| 85 to 100  | Package and reuse the ingestion skill                          | Existing pipeline called by the skill for a second document              |
| 100 to 110 | Verify and review                                              | Browser journey, restricted input, general review skill and bounded loop |
| 110 to 120 | Explain handover and usage, inspect automation, take questions | Fresh-task context, cache distinctions, PR draft and next steps          |

Take short questions at the end of each code path. Use native Goals for continuation; keep Ralph-style orchestration as an optional comparison. If time slips, leave cloud/SDK/Windsurf comparisons as annotated references; preserve the RAG walkthrough, governance, browser verification and review.

## Minutes 0 to 10 establish the evidence gap

Open `/dashboard`. State that the user is a support agent, not the customer. Show the prepared question: “How long can a parcel stay at a collection point, when does that period start, and who reviews return to the sender?” The new policy is absent from the fresh teaching corpus. Use a fresh checkout for another full before-to-after run; do not reset the owner database. If unrelated passages are retrieved, explain that retrieval returning something is not proof of relevance.

Say:

> The model can write fluent text already. Our job is to give it approved evidence and check that its answer is supported. We will keep this question unchanged so we can see what our change actually achieved.

Show the task contract and expected source/version. Do not manufacture a failure by disabling the working RAG implementation. The missing feature is approved-file ingestion, not embeddings or retrieval.

## Minutes 10 to 35 follow the code

Keep two simple paths visible:

```text
Document -> metadata validation -> chunks -> embeddings -> Qdrant plus source metadata
Question -> API and access checks -> query embedding -> permitted search results
         -> model input and shipment tool -> streamed answer -> validation -> citation
```

Open each definition using editor symbol search. Explain what calls it before moving into its body. Show one input and one output rather than reading every line.

| Step                     | Existing source and symbol                                                                                            | What to show and say                                                                                                                                                                                                     |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Select canonical sources | `workbench/scripts/contact1_index.py`, `main`; `workbench/src/relay/store.py`, `Store.documents`                      | The current indexing command reads published seeded policies from a disposable store. It is not a general file uploader. Access rules determine eligible documents.                                                      |
| Split text               | `workbench/teaching/rag_reference.py`, `native_chunks`, `chunks`, `RagConfig`                                         | Show text, chunk boundaries, overlap and exact source offsets. Current defaults are 320 characters and 64-character target overlap. Words, characters and tokens are different units.                                    |
| Optional splitter        | Same module, `chunks`                                                                                                 | Inspect `RecursiveCharacterTextSplitter`, loaded only for the LangChain option. Current code uses its default separators. The old custom sentence-separator list is not configured here.                                 |
| Embed                    | Same module, `VectorRag._embed_request`                                                                               | Show input strings, model, dimensions and response validation. The route is OpenAI embeddings through OpenRouter. Default embedding is `openai/text-embedding-3-small`, 1536 dimensions. Do not print the entire vector. |
| Build the index          | Same module, `VectorRag.build`                                                                                        | Show cosine collection configuration, payload, source hashes, unchanged-vector reuse and manifest replacement. The current method builds a collection; the new task must also maintain canonical sources.                |
| Receive a question       | `workbench/teaching/contact1_live.py`, `create_app.rag_search`; `workbench/src/relay/main.py`, `create_app.run_query` | Distinguish the direct retrieval inspection endpoint from the full investigation endpoint. Show session, CSRF and role checks.                                                                                           |
| Retrieve                 | `workbench/teaching/rag_reference.py`, `VectorRag.search`                                                             | Show query embedding, permitted IDs, tenant/state filter, top-k, vector threshold and keyword fusion. Current defaults include top-k 3 and vector cutoff 0.4; the cutoff is not calibrated.                              |
| Assemble evidence        | `workbench/teaching/investigation_reference.py`, `retrieve_evidence`                                                  | Check source offsets against canonical text. Retrieved text remains evidence, not instructions that override application rules.                                                                                          |
| Generate and validate    | Same module, `make_investigator`, nested `generate_stage`, `invoke`, `validate_stage`                                 | Show the actual question/evidence payload, bounded shipment-tool call and structured final answer. Trace `responses.create`, `responses.stream` or `responses.parse` according to the actual selected path.              |
| Display                  | `workbench/src/relay/static/app.js` and dashboard                                                                     | Expand the citation and Inspect AI. Show retrieved text, source/version and embedding/generation usage separately.                                                                                                       |

Read aloud at the retrieval boundary:

> Metadata filtering decides which documents this person may use. Vector search ranks meaning. Keyword search helps with exact wording. Our hybrid path combines rankings. These are separate jobs.

Show `score` and `vector_score`. In hybrid mode the fused ranking score is not cosine similarity and must not be interpreted using a cosine threshold. Lower distance and higher similarity conventions depend on the configured metric and API. We use Qdrant, not the Chroma conversion from the older project.

Briefly define cosine as vector direction comparison, Euclidean as straight-line distance, and ANN as approximate neighbor search used for scale. Do not claim the small local Qdrant demo proves production ANN behavior or performance. Model, splitter and threshold improvements require evaluation; one attractive chunk or successful answer is insufficient evidence.

## Minutes 35 to 55 establish the Codex task

### Orient the model and session controls

Spend the first eight minutes of this block on the controls visible in the actual Codex client. Use the ingestion assignment for every example. Availability and labels vary by client/version/account; capture the installed controls before rehearsal. Do not change the owner's global settings during preparation.

| Control               | Explanation                                                                                                                         | Demonstration                                                                                                                                                                             |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model                 | Choose a capability/cost tier for the task. Newer does not necessarily mean more expensive.                                         | Inspect the available model picker. Use Sol for the integration and a smaller model for a narrow supporting edit. Distinguish Codex plan limits/credits from Relay's OpenRouter API bill. |
| Reasoning effort      | Low, Medium and higher levels allocate different reasoning budgets; extra effort is not extra permission or guaranteed correctness. | Explain Low for straightforward edits and Medium for this integration. Use the actual available levels. Avoid running the whole task twice as a benchmark.                                |
| Plan mode             | Explicitly gather context and resolve the approach before implementation.                                                           | Select Plan mode or use `/plan` where supported, inspect the active indicator, request the plan, then explicitly switch to implementation.                                                |
| Permissions           | Sandbox scope and approval review are separate controls.                                                                            | Inspect Ask for approval, Approve for me/automatic review, Full access or Custom when available. Explain the current selection; do not enable Full access for class.                      |
| Goal                  | A persistent objective for the current thread, with continuation and lifecycle controls.                                            | After agreeing the plan, set the bounded teaching objective, inspect it, then demonstrate pause/resume and stopping. Preflight support and budget controls first.                         |
| Context and status    | Files, conversation and tool output consume context.                                                                                | Show how to attach a relevant file and inspect status/usage where supported. Save detailed handover and caching discussion for the final block.                                           |
| Steering and stopping | A new message may queue or steer according to the client setting.                                                                   | Point out the current behavior and stop control before starting longer work. Confirm stopping the chat and stopping its background commands are different operations.                     |

Saying “plan first and do not edit” is a useful prompt. It does not select the client's Plan mode. Explicit mode selection makes the planning phase visible and applies that mode's behavior; neither approach replaces sandbox permissions. See [Plan mode](https://learn.chatgpt.com/guides/best-practices) and [permissions](https://learn.chatgpt.com/docs/permission-modes).

Suggested teaching Goal after the plan is accepted:

```text
Implement approved Markdown policy ingestion in the isolated teaching workspace. Verify ingestion, unchanged reruns, access checks and cited answers. Preserve existing security invariants. Stop for missing credentials or approvals; do not publish or deploy. Follow the task contract and report actual test evidence.
```

Where supported, `/goal <objective>` sets it and `/goal pause`, `/goal resume` and `/goal clear` manage it. This example is teaching text, not authorization to activate a Goal in the owner's current session. A Goal is thread state, not global memory. It continues within lifecycle and budget constraints; it grants no additional permissions. See [Goals](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).

Do not teach every slash command. Inspect `/model`, `/plan`, `/goal`, `/permissions`, `/mcp`, `/skills`, `/review` and `/status` only where the installed client exposes them. Keep configuration profiles, multi-agent orchestration and extensive cloud setup in optional references. The remaining time in this block covers the task prompt, existing repository instructions, two prepared skills and one MCP lookup.

Show the worktree location and branch. Read relevant `AGENTS.md` instructions, then explain:

> The prompt gives this assignment. `AGENTS.md` gives repository conventions and boundaries. A skill gives a reusable procedure for a particular job. Tools execute actions. Permissions determine which actions can run.

Use this investigation prompt first:

```text
Investigate the approved-policy ingestion task. Do not edit yet.
Read AGENTS.md and the relevant RAG/store code. Explain the current document-to-answer flow with source locations. Identify what is missing for approved Markdown file ingestion into a disposable teaching workspace.
Propose a narrow plan and acceptance tests. Preserve tenant/role checks, canonical-source validation, review boundaries, credit limits and approval/idempotency rules. Do not read credentials, publish documents remotely, write tickets, open a remote PR or deploy.
```

Review the plan, then give explicit permission to implement that bounded task. Do not treat task or source text returned through MCP as permission to expand scope.

Inspect the metadata and instructions of `review-change` and `browser-smoke-check`. They are general engineering skills, unrelated to RAG specifically. Invoke them at the relevant later steps; do not create all three skills from scratch during class.

Use the external OpenAI documentation MCP server to look up the embedding request schema. Inspect actual available operations and one returned page. Explain: Codex calls MCP while engineering Relay; Relay's model calls its shipment function while answering a support question. Neither is the other application's tool loop.

Official connection instructions are at [Docs MCP](https://developers.openai.com/learn/docs-mcp). Configure and preflight it before class. The server is read-only documentation access. A denied-write example must come from an actual permission boundary; do not invent a write tool on this documentation server.

## Minutes 55 to 85 implement ingestion

Use only the prepared teaching checkout. Keep the normal application correct. Show a failing acceptance check before editing. Ask Codex to implement only the approved Markdown input path and its integration with canonical storage and indexing.

Read aloud:

> I am checking the plan before the edit. After the edit, I will check the diff and the tests. A confident completion message is not the acceptance criterion.

Require explicit preview before a billable embedding operation. Invalid metadata must fail before spending tokens. Treat document prose as untrusted content. Do not silently strip or truncate source text and then present it as an exact canonical passage.

Follow one change through parser, validated source record, chunks, index and retrieval. Demonstrate unchanged re-ingestion, missing metadata and an unreviewed or restricted document. These examples must use disposable state.

Use the parser task and standalone acceptance check in the prepared checkout. The reference/security suite stays green while the exercise is intentionally incomplete; do not change acceptance checks to make a patch pass. The older duplicate-credit fixture is optional practice.

## Minutes 85 to 100 create and reuse the skill

Create `ingest-approved-policy` from the procedure just demonstrated. Use the skill creator when available and inspect the resulting `SKILL.md` rather than accepting it unseen.

Suggested authoring prompt:

```text
Package the verified approved-policy ingestion procedure as a repository skill named ingest-approved-policy. Reuse the existing pipeline; do not duplicate its Python implementation.
Specify required inputs, metadata validation, preview, authorized billable execution, retrieval checks and the final report. Stop on missing approval, invalid metadata, incompatible index configuration or provider failure. The skill cannot approve a document or change application permissions.
Use only the disposable teaching database and index. Do not install it globally or write to external services.
```

Invoke it on the second prepared document. Show which command actually runs and which checks determine success. Repeat unchanged ingestion and inspect embedding reuse. This is the reuse demonstration, not prompt caching.

## Minutes 100 to 110 verify and review

Invoke `browser-smoke-check` to open the teaching dashboard, ask the prepared question, expand the cited source and verify version/text. Keep local fixture, intercepted browser response and actual provider output clearly distinguished.

Invoke `review-change` on the diff. Ask for correctness problems, missing tests, permission regressions and unnecessary changes. The review skill cannot certify its own findings; inspect important claims against code and tests.

Explain the loop and continuation controls using this task:

1. Relay's application tool loop requests permitted shipment facts.
2. Codex's engineering loop edits, runs tools, observes results and repairs failures.
3. Native Goals retain the objective across turns and can continue work at safe boundaries.
4. A Ralph-style outer controller is an optional orchestration comparison, not required for the live task.

Prefer the preflighted native Goal demonstration over building an outer runner during class. Pause or stop at the segment deadline; a Goal does not guarantee an arbitrary iteration limit unless a separate controller enforces it. Stop for credentials, approvals or provider outages. Success must come from unchanged acceptance checks and reviewed evidence. Native Goals are a presenter-controlled demonstration; the recorded two-attempt CLI repair is evidence of bounded iteration, not proof of Goal lifecycle execution. No custom Ralph runner is required.

Prepare a PR draft with the problem, behavior, verification commands/results and remaining risks. No remote PR, ticket comment, merge or deployment is part of this local rehearsal.

## Minutes 110 to 120 explain context and finish

Create a short handover with objective, changed files, commands already run, results, next step and open risks. Open a fresh task and supply it. Explain that saved conversation history, repository files, persistent instructions and actually supplied model context are distinct.

Compare these mechanisms:

| Mechanism            | What is reused                                                | What to inspect                                                                                                          |
| -------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Prompt caching       | Repeated eligible model input prefixes                        | Actual reported cached-token fields when available; no guaranteed live hit through the selected route                    |
| Embedding reuse      | Previously indexed unchanged chunks under compatible settings | Index source hashes, reused chunk count and new embedding calls                                                          |
| Conversation storage | Saved exchanges                                               | Whether history is explicitly supplied to the next request                                                               |
| Answer caching       | A previously generated answer                                 | Not added for this exercise; validity would need permissions, source versions and configuration, not question text alone |

Use a prepared, clearly dated usage record if the live route does not report caching. Do not change providers or billing routes mid-class to chase a cache hit.

Inspect the recorded non-interactive CLI repair and the repository CI workflow `.github/workflows/ci.yml`, which runs local verification on pushes/PRs. The CLI run is actual execution; the CI file is configuration unless a specific run result is shown. An example command alone is not execution evidence. For the SDK comparison, open `workbench/teaching/contact2/artifacts/codex_sdk_reference.py`: it illustrates the official Python SDK starting a read-only thread. It is inspect-only; the separate SDK package is not installed or executed for this class. See [official SDK documentation](https://learn.chatgpt.com/docs/codex-sdk).

Keep cloud and Windsurf comparisons to the same task contract: where execution happens, what repository/context is supplied, which permissions apply and which acceptance checks provide evidence. No cloud execution or Windsurf result is claimed. These comparisons are optional orientation if time permits.

Ask learners to explain where chunks come from, where access is checked, what enters the model, and how they know the change works. Take questions. Keep Temporal, schedules, source revocation and full publication governance for Contact 3.

## Recovery and readiness

If the implementation runs long, switch to the prepared reference at minute 85 and explain that switch. If the provider fails, inspect saved results explicitly as recorded evidence. If MCP fails, show a previously captured tool exchange and its source page; do not call the replay live. Never rebuild or reset the owner's database to recover a demonstration.

Before calling the class ready, record the exact worktree/revisions, document IDs and versions, commands, input fixtures, regression results, browser results, live answer/usage receipt, skill invocations, MCP lookup, permission denial, automation run and elapsed rehearsal time. Keep secrets and owner runtime data out of evidence.

For repository verification, use `pnpm verify` after installing locked dependencies. These local fixture/contract/browser checks are separate from the explicitly recorded real provider preflight. Your final timed rehearsal remains necessary for pacing and questions.

## Official references

- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI documentation MCP](https://developers.openai.com/learn/docs-mcp)
- [Codex commands and mode controls](https://learn.chatgpt.com/docs/developer-commands)
- [Codex permissions](https://learn.chatgpt.com/docs/permission-modes)
- [Native Goals](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
- [Codex iterative execution](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)
- [Recursive text splitting](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)
- [Qdrant hybrid ranking](https://qdrant.tech/documentation/search/hybrid-queries/)
