# Separately verified teaching references

These modules are opt-in and are not imported by the baseline app. Install SDKs with `uv sync --project workbench --locked --extra references` from the repository root. Unless stated otherwise, commands below run from `workbench`.

## Contact 1

Start with the [Contact 1 preparation guide](../../docs/teaching/CONTACT_1_PREPARATION.md) for the three launch profiles, integrated live provider, bounded evaluation, tracing setup and timed demonstration. `pnpm contact1:before`, `pnpm contact1:retrieval` and `pnpm contact1:live` run from the repository root.

Before state: default app on port 8000; title-only retrieval. The fixture paraphrase “My parcel arrived overdue, any goodwill?” abstains.

Intermediate inspection: read `contact1_reference.py`, compare its FTS passage/tag search and minimum lexical evidence threshold. The threshold is a small synthetic-fixture heuristic, not a semantic relevance guarantee.

Intermediate lexical server, independent database and port:

```sh
PYTHONPATH=. .venv/bin/python -m uvicorn teaching.contact1_reference:create_app --factory --host 127.0.0.1 --port 8001
```

Open a fresh browser workspace at port 8001; `/api/health` identifies the reference. It searches the authorized published corpus only. This is lexical fixture retrieval, not embeddings or live generation.

`rag_reference.py` keeps compatibility imports; the shared implementation is organized under `contact2/indexing/` and `contact2/querying/`. These stages implement OpenAI embeddings, deterministic versioned chunks, persistent local Qdrant, authorization filters before top-k, index reuse/freshness and vector/hybrid retrieval. Run `pnpm contact1:index` before `pnpm contact1:live` (root commands with configured credentials). Live `/docs` includes index status and protected retrieval inspection endpoints. The actual local-store/SDK-mock tests do not establish live semantic quality.

`investigation_reference.py` is the application runtime: scoped caller-managed history, fixed/agent tools, direct/LangGraph stages and structured validation. The live UI exposes these choices and uses actual provider streaming with progress/final-result events. `observability_reference.py` wraps execution stages and exports nested redacted Langfuse observations; tests include its actual SDK and a local OpenTelemetry exporter. `semantic_evaluation.py` and `review_evaluation.py` separate model judgments from revision/run-bound human labels. The [coverage audit](../../docs/teaching/CONTACT_1_COVERAGE_AUDIT.md) records both corrected and still-open scope.

`responses_reference.py` implements a small independently tested SDK structured-output boundary; `tool_loop_reference.py` implements a bounded read-only function loop. Fake-client and actual SDK HTTP-mock tests run without network. They prove contracts/authority, not live model quality or semantic support for every claim.

Actual opt-in smoke from the repository root, after configuring environment variables locally:

```sh
RELAY_ALLOW_LIVE=1 uv run --project workbench --locked --extra references python workbench/scripts/live_smoke.py
```

`OPENAI_API_KEY` and `OPENAI_MODEL` must already be set, and `pnpm contact1:index` must have prepared the corpus. The compatibility smoke now delegates to the complete RAG preflight, rather than testing only a supplied passage/schema. This makes bounded billable calls; normal tests never run it. No live smoke result is recorded until actually executed with provisioned access. Actual nested Langfuse SDK instrumentation is tested locally, not proof of a hosted trace upload.

### OpenAI state strategies

`openai_state_reference.py` is a separate two-turn synthetic SDK comparison of stateless input, manual history, `previous_response_id` and Conversations. It does not change Relay's caller-managed case memory or source checks. Run `pnpm contact1:state --mode conversation --live` from the root only after configuring the explicit live opt-in/model/key. See the preparation guide for env-file loading and limits. Provider-managed modes attempt bounded cleanup, with failures disclosed. SDK/mock HTTP tests establish request lineage and cleanup attempts; live recall/retention are unverified. Use pre-run output for the short in-class comparison, not four additional live experiments.

### Preparation experiments

`conflict_reference.py` plus `pnpm contact1:conflict` runs a controlled, disposable conflicting-policy corpus through the real API/vector investigation. `pnpm contact1:compare --alternate-model MODEL` reserves two experiments on the six-case exploratory draft subset (24 generation / 12 query embeddings maximum). Both preserve the operational corpus and the owner's cases, and require facilitator review of generated claims. `pnpm contact1:collector` verifies actual metadata-only Langfuse receipt without invoking a model. It is not proof of a live AI investigation. These commands load no `.env` implicitly; use exported variables or the preparation guide's `uv --env-file` form.

## Contact 2

The main RAG demonstration is the working PDF upload flow at `/teaching/contact-2`. Start at `contact2/indexing/pipeline.py`: `preview_pdf` calls parsing/chunking for review; `build_index` explicitly calls chunking, embedding and Qdrant storage. Upload/review records and removal live separately in `contact2/document_service.py`; canonical sources and transactional publication are in `contact2/policy_store.py`. Its sibling modules contain PDF parsing, chunking, embedding requests and Qdrant storage. `contact2/querying/pipeline.py` is the direct policy-query entry: `answer_question` calls `retrieve_passages`, `generate_answer` and `validate_answer`. The API is `POST /api/v1/policies/query`; it has no case ID or investigator callback. Retrieval and answer implementations are in sibling `retrieval.py` and `answer.py`. The case-based runtime retains its adapters separately in `investigation_answer.py` and `investigation_retrieval.py`. The former `pdf_pipeline.py` and duplicate root `pipeline.py` have been removed. The separate Markdown preview is in `markdown_practice.py`. The UI shows actual text, chunks, stored vectors, retrieved passages and cited answers on one page. A downloadable original sample is in `contact2/pdfs/`; regenerate it with `scripts/contact2_sample_pdf.py`. `scripts/contact2_pdf_preflight.py --confirm-billable` verifies the real provider using disposable data. The optional Markdown exercise remains incomplete independently of PDF ingestion.

The main session is the [120-minute practical AI engineering and governed Codex rehearsal](../../docs/teaching/CONTACT_2_REHEARSAL_GUIDE.md): a working PDF walkthrough followed by a page-reference improvement. The replacement exercise, completed fallback and PDF skill reuse still need preparation; the three-page sample is available under `contact2/pdfs/`. `contact2/TASK.md` and its parser reference describe the older Markdown exercise, retained as separate practice rather than the current class assignment.

The original duplicate-event red/green fixture below remains optional practice, not the main session:

```sh
PYTHONPATH=. .venv/bin/python teaching/contact2_regression.py --state before
PYTHONPATH=. .venv/bin/python teaching/contact2_regression.py --state reference
```

The first command intentionally exits 1 (₦4,000 actual versus ₦2,000 expected); the second exits 0. The actual baseline service never imports the broken fixture. `codex-task.md` is the issue/PR task contract. `mcp_reference.py` exposes one read-only fixture ticket through the actual MCP SDK:

```sh
PYTHONPATH=. .venv/bin/python -m teaching.mcp_reference
```

This is a stdio server intended for an MCP client, not an HTTP page. Tests exercise allowed/denied calls in process through the SDK protocol. No real Linear/GitHub account is connected. Codex CLI/cloud/non-interactive examples require account preflight and their own actual execution evidence.

## Contact 3

```sh
PYTHONPATH=. .venv/bin/python -m uvicorn teaching.ingestion_reference:create_app --factory --host 127.0.0.1 --port 8003
```

The independent review API is available in `/docs`. POST candidate JSON to `/api/v1/review/candidates` with an agent session/CSRF token; switch the same workspace to supervisor to inspect and publish. Candidate content does not become retrievable until publication. This is a local synthetic review workflow; demo persona switching is not real identity assurance.

Completed skill: `skills/relay-review-policy/SKILL.md`. It is packaged here for review, not installed into global agent discovery. The separate `AGENTS.before.md` and `AGENTS.reference.md` preserve the live authoring exercise. `component_reference.py` runs actual LangChain chunking and a small LangGraph review-state graph; it is not an LLM-powered agent.

`temporal_reference.py` defines an actual durable approval workflow and an Africa/Lagos 09:00 freshness schedule definition with overlap skipped and bounded catch-up. Importing/inspecting it registers no schedule. The approval signal must be sent by an authenticated backend in a real integration; a local Temporal service is not an authorization system.

Actual local server/worker restart test from repository root:

```sh
RELAY_TEMPORAL_TEST=1 uv run --project workbench --locked --extra references pytest workbench/tests/test_temporal_live.py -q -s
```

The approval test downloads/runs the official test server, stops the worker while awaiting review, sends duplicate approval signals and resumes with a new worker. A unique activity ledger records one effect. The schedule test starts an ephemeral local dev server, registers the schedule, triggers a run immediately, checks its result, pauses it and deletes it. This proves local workflow recovery and the schedule API lifecycle, not production Temporal cluster persistence or a wall-clock recurring execution. No active schedule remains. The SDK’s fixed five-second dev-server startup check was intermittent on cold launch. The schedule harness now pins CLI 1.9.1, waits explicitly for gRPC readiness with a 30-second limit, and always tears down its process. Preflight startup before class.

## Remaining delivery preflight

The baseline and references have local verification evidence. The full expanded course is not yet class-ready: actual OpenAI quality/usage, live retrieval calibration and advanced reranking experiments, Langfuse export, real ticket/PR/cloud workflows, customer discovery/review, full timed rehearsal and advanced practice implementations still need their own evidence. See `../checkpoints.json` and the coverage blueprint. No unavailable result should be presented as a passing live integration.

OpenRouter is an opt-in billing route (`RELAY_AI_PROVIDER=openrouter`, separate `OPENROUTER_API_KEY` and namespaced OpenAI model IDs). It shares the Responses/embeddings runtime and defaults to a separate vector directory. Native stored-state exercises are gated; see the [preparation guide](../../docs/teaching/CONTACT_1_PREPARATION.md#openrouter-billing-route). Mock gateway transport tests do not establish live compatibility or quality.
