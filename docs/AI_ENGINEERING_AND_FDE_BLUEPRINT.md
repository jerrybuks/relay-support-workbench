# AI engineering and FDE teaching blueprint

Research date: 19 October 2026. Status: expanded curriculum adopted; Relay baseline and selected references verified locally. Full delivery readiness still requires the preflight, review and practice gates recorded in the active design and Relay evidence.

The owner extended Contact 2 to two hours on 22 October 2026. That session-specific allocation supersedes the original four-hour budget; the other three contacts remain one hour each.

## Intent and relationship to the original specifications

The owner has expanded the teaching scope beyond the game specification. Participants are likely comfortable with ordinary backend/API engineering. Prepare that foundation before class and explain it briefly. The practical project must expose AI engineering, reliable delivery with Codex, and forward-deployed engineering (FDE) decisions through understandable business workflows.

This document records the expanded scope and a proposed allocation. It does not claim that four hours establishes independent proficiency across every topic. Provide broad orientation, selected live engineering demonstrations, inspected reference implementations, and guided practice with verifiable outcomes.

Retain the original requirements for four 60-minute contacts, approximately 15 minutes of slides and 45 minutes of facilitator-led engineering in Contacts 1–3, meaningful RAG work in Contact 1, controlled Codex delivery in Contact 2, governed ingestion/skills in Contact 3, and evidence/certification readiness in Contact 4. Optional participant work starts after Contact 3; Contact 4 does not require presentations. Live changes must remain available at before/intermediate/reference checkpoints.

The earlier game is retained only in historical Git checkpoints. The owner questioned its suitability and authorized the replacement; its mechanics and TypeScript-only architecture are not requirements for Relay. Relay and its FastAPI foundation are the active implementation. Relay, a fictional logistics support-resolution workbench, has now been selected against this matrix. The [product design](PRODUCT_AND_TECHNICAL_DESIGN.md) and `workbench/checkpoints.json` distinguish implemented, locally verified and still-pending capabilities.

## Coverage and evidence matrix

Modes: **live** = execute/explain or improve a prepared scenario during class; **inspect** = explain a prepared implementation/report; **practice** = supplied guided exercise/reference, with completion assessed separately. Each topic has a place; live depth varies.

| Area                      | Required coverage                                                                                                                                        | Contact and mode                    | Evidence or exercise outcome                                                                       |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------- |
| FDE discovery             | User/workflow discovery, pain and business baseline, stakeholder/data owners, AI suitability, scope and non-goals                                        | C1 inspect; C4 decision exercise    | One-page discovery brief, workflow map, measurable success criteria                                |
| API foundation            | FastAPI/OpenAPI, contracts, auth, tenant/role permissions, rate limits, streaming, error handling, idempotency, versioning                               | Prepared; C1 brief inspect          | Working frontend/backend, documented routes, tests and seeded roles                                |
| OpenAI fundamentals       | Responses, SDK, model selection, reasoning/verbosity controls where supported, structured outputs, refusal and incomplete output handling                | C1 live                             | Validated response and visible failure handling; configuration snapshot                            |
| Prompts and context       | Instruction hierarchy, prompt versions, examples, trusted/untrusted content, context selection and token budgets                                         | C1 live; C3 inspect                 | Versioned prompt and adversarial context test                                                      |
| RAG ingestion             | Parsing HTML/PDF/images, extraction confidence, chunking alternatives, metadata, embeddings, index readiness, provenance/rights                          | C3 live; C1 inspect existing corpus | Candidate review queue, page-level source mapping, duplicate rejection                             |
| Retrieval quality         | Keyword/vector/hybrid search, filters before context, reranking, query rewriting, chunk/context experiments, freshness and deletion                      | C1 live; practice                   | Retrieval report with recall/ranking measures, citation correctness and access tests               |
| Grounded answers          | Evidence support, citations, conflicting or outdated policies, abstention, uncertainty and escalation                                                    | C1 live                             | Golden cases distinguish no evidence, contradictory evidence and supported answers                 |
| Tool calling              | Schemas, argument validation, execution/result loop, read/write split, parallel versus dependent calls, unavailable tools                                | C1 live; C3 inspect                 | Tool trace, invalid-argument test and denied unauthorized call                                     |
| Agent execution           | Deterministic workflow versus agent, bounded loops, stopping criteria, budgets, handoffs and multi-agent coordination                                    | C1 inspect; C3 live; practice       | Inspectable run graph, loop-budget failure, single/multi-agent comparison                          |
| State and memory          | Stateless versus stateful requests, conversation continuity, business state, workflow checkpoints, long-term memory, compaction, retention/deletion      | C1 live; C3 inspect; practice       | Resume test, isolated users, deletion check, long-context comparison                               |
| Skills and instructions   | AGENTS.md scope, SKILL.md trigger/instructions/resources, progressive loading, versioning, skill tests, plugins/distribution                             | C3 live; practice                   | Reusable reviewed-source skill with fixtures and explicit output contract                          |
| MCP and integrations      | Client/server boundary, tools/resources/prompts, local/remote transport, identity/scopes, untrusted tool output, permission review                       | C2 live; C3 inspect                 | Scoped ticket/document integration, denied operation, sanitized trace                              |
| Scheduling and events     | Scheduled versus event-triggered execution, timezones, overlapping runs, missed runs, deduplication, pause/cancel and review                             | C3 live; practice                   | Trigger once on demand, inspect schedule, duplicate-event test; no waiting for wall clock in class |
| Long-running work         | Background responses, polling/events, signed webhooks, cancellation, Temporal workflows/activities, approval waits, retries and side effects             | C3 live; practice                   | Worker restart/resume, webhook verification, duplicate action prevented                            |
| Guardrails/security       | Prompt injection, data leakage, moderation versus business policy, tool-boundary authorization, approval of exact proposed action, sandbox/egress limits | C1 live; C3 live; C4 incident       | Red-team cases, access denials, approval record and failure-closed test                            |
| Evaluation                | Golden set, provenance and reviewer, held-out cases, code graders, calibrated model judges, humans, repeated runs, slice analysis                        | C1 live; C4 inspect; practice       | Versioned dataset and harness; before/after results with disclosed provider and uncertainty        |
| Agent evaluation          | Tool choice/arguments, action sequence, approval compliance, task completion, cost per successful task                                                   | C3 inspect; C4 decision             | Full-run evaluation, not just final-answer grading                                                 |
| Observability             | Langfuse traces/spans/sessions, prompt/model/corpus versions, request IDs, redaction, token/cost/latency and failure categories                          | C1 live; all contacts               | Trace linked to test/run and version; no sensitive payloads or hidden chain-of-thought             |
| Optimization              | Model routing, supported reasoning settings, prompt caching, batch/flex trade-offs, retrieval/generation bottlenecks and fallback quality                | C1 inspect; C4 compare; practice    | Same-dataset comparison of quality, p95 latency and cost per success                               |
| Codex delivery            | Repository explanation, planning, reproduce/test/fix loops, scoped diffs, review, documentation, local/cloud work, worktrees, delegation boundaries      | C1 intro; C2 live                   | Ticket → failing test → patch → passing checks → reviewed PR; stop conditions recorded             |
| Programmatic Codex        | Non-interactive execution, SDK, CI integration, structured results, controlled runtime, integrations with Linear/GitHub                                  | C2 live/inspect; practice           | Reviewed automation output in isolated branch; no automatic merge or unrestricted ticket writes    |
| Browser and computer use  | Playwright assertions versus model-driven browser/computer interaction, UI-state validation, credentials and confirmation boundaries                     | C2 live; advanced practice          | Reproduce and verify user journey in browser; bounded computer-use reference                       |
| Governance and operations | Least privilege, secrets, project controls, data residency/retention, audit, CI/CD, staged rollout, incident response, rollback and ownership            | C3 inspect; C4 decision             | Release pack, runbook, access/retention matrix, rollback rehearsal                                 |
| Multimodal and realtime   | PDF/vision provenance; audio/transcription/voice and realtime transport/turn-taking/cancellation                                                         | C3 inspect; practice                | Small document/image reference and voice extension with disclosed limitations                      |
| Model adaptation          | Prompt/context/RAG versus fine-tuning/distillation; data suitability, supported methods, held-out evaluation and lifecycle                               | C4 inspect; practice                | Decision record and reproducible comparison where platform/account support permits                 |
| Alternative tooling       | LangChain components, LangGraph state/decisions, OpenAI Agents SDK/managed runtime comparison, Windsurf workflow comparison                              | C1/C2/C3 inspect; practice          | Architecture comparison explains boundaries and measures the same task                             |
| FDE adoption and handover | Discovery → thin vertical slice → pilot → iteration → rollout; user training, integration constraints, outcome measurement and support ownership         | C4 decision; practice               | Pilot plan, stakeholder acceptance, handover and follow-up outcome measurement                     |

## Runtime boundaries and tool roles

Use one primary application execution path. Framework comparisons and advanced runtimes can have separate prepared references; installing multiple frameworks is not evidence that participants understand them.

- FastAPI owns application contracts, identity, authorization and business invariants. The frontend makes the user workflow and AI evidence easy to follow.
- Responses is the primary model integration. Compare direct calls, the application-hosted Agents SDK, and the managed Agents API as runtime choices. Confirm account access, cost, retention and feature status before preparing examples.
- LangChain can provide a defined retrieval/component role; LangGraph can demonstrate explicit agent state/branching. Temporal owns a separate durable business workflow or is presented as an alternative reference. Avoid two independent engines retrying the same external mutation.
- Langfuse exposes traces, versioned experiments and evaluations. Retain project-owned datasets and reproducible reports so a dashboard outage does not erase evidence.
- MCP supplies bounded access to external capabilities. Skills describe reusable methods; AGENTS.md supplies repository instructions; backend code enforces authority. None of these replaces the others.
- Codex is the main engineering agent. Windsurf gets a comparison using the same acceptance criteria, without duplicating the entire delivery demonstration.
- Scheduling supplies triggers. Temporal supplies durable execution. Background model requests supply asynchronous inference. These are distinct responsibilities, not interchangeable features.

## Scheduling and skill demonstration

Prepare a recurring document/policy freshness check. A skill defines how to check sources, detect changes, produce a reviewable report and propose follow-up work. A schedule or supported event determines when it runs. A human reviews publication or external changes; the demonstration uses a disposable fixture or approved sandbox.

Show manual invocation first, inspect the scheduled configuration, then trigger an equivalent run immediately. Include timezone, overlap policy, run ID, retries, duplicate-event handling, missed-run policy, next-run visibility, notification destination and pause/cancel. Do not create real recurring jobs or send external messages as part of preparing this blueprint.

Demonstrate both developer productivity automation (for example, scheduled Codex regression triage with reviewed output) and an application-owned business schedule. Explain local-machine availability and account/plan prerequisites for desktop/cloud automation. Freeze exact UI paths during preflight, because current Codex automation and skill URLs redirect to the unified ChatGPT Learn documentation.

## Contact flow and time budget

### Contact 1: grounded AI application engineering

- 0–15: business problem/success criteria; existing API and trust boundaries; Responses/tools/state/RAG choices; evaluation contract.
- 15–23: run a prepared failure and inspect trace, retrieval and baseline results.
- 23–38: make one bounded retrieval/grounding improvement; inspect structured answer, citations and a representative read-only tool call.
- 38–48: test unauthorized evidence, unsupported query and model/tool failure; inspect state continuity and guardrail enforcement.
- 48–55: compare fixed evaluations and quality/latency/cost; explain remaining risks.
- 55–60: basic Codex repository explanation and bounded next task.

Prepared inspection materials cover ingestion, routing/caching and alternative runtimes. Deeper experiments have guided references. Do not promise to build all of these live.

### Contact 2: RAG implementation and governed Codex delivery

The owner extended Contact 2 to 120 minutes. Use the [rehearsal guide](teaching/CONTACT_2_REHEARSAL_GUIDE.md): trace ingestion/retrieval in code, implement one approved-file ingestion parser, package a reusable skill, verify the cited answer and review the delivery evidence. Teach model/effort, Plan mode, Goals, permissions, AGENTS.md, general engineering skills, MCP, context, caching, worktree isolation and bounded repair through that one task.

The duplicate-event fixture remains optional practice. Native Goal support is detected but lifecycle operation belongs to the presenter rehearsal. Cloud, SDK and Windsurf examples are reference comparisons, not claimed live executions. External ticket/PR writes require separate task authorization.

### Contact 3: governed ingestion and durable automation

- 0–15: skill/MCP/state/workflow boundaries, ingestion governance and schedule/event model.
- 15–30: use Codex and a skill to improve a prepared ingestion candidate/review path; exercise duplicate, missing-provenance and malicious-content fixtures.
- 30–40: review/publish authorized material and show retrieval freshness plus memory/tenant separation checks.
- 40–52: trigger the prepared scheduled workflow, pause for approval, restart its worker and resume safely. Show deduplication and denial on rejected approval.
- 52–60: inspect full-run trace/evaluation, audit evidence and reference PR; introduce optional practice.

The durable workflow and scheduling infrastructure must be built and tested before class. The live implementation remains a narrow ingestion/governance improvement. Advanced agent loops, multi-agent and realtime references are supplied separately.

### Contact 4: FDE readiness and deployment judgment

- 0–10: revisit customer baseline, outcomes, assumptions and stakeholder acceptance.
- 10–25: inspect quality/security/cost evidence; decide pilot scope and release gates.
- 25–40: incident and recovery exercise: stale source, revoked permission, duplicate event, model outage or interrupted approval.
- 40–50: rollout/rollback, training, operational handover and adoption measurement; compare advanced options including model adaptation and voice/multimodal.
- 50–60: separate OpenAI API and Codex certification-readiness checks and individual follow-up plan. No required learner presentations.

## Before-class preparation and acceptance

1. Select a product with an understandable business workflow, permissioned documents, read-only tools, one approval-gated action and a plausible recurring task. Write discovery brief, non-goals and success measures before implementation.
2. Prepare a working FastAPI/application baseline with seeds, OpenAPI, basic API controls, dependency locks, repeatable environment/setup, and automated smoke/browser checks. API mechanics are assumed knowledge.
3. Prepare separately verified before/intermediate/reference states for each live engineering contact. Include exact revision, reset commands, seed/data versions, fault injection, expected outputs and recovery steps. Preserve the current game tags as historical artifacts.
4. Prepare reviewed corpus and evaluation data, including held-out and adversarial cases. Set numeric thresholds after establishing a measured baseline; do not invent a pass rate or call a synthetic dataset customer-validated.
5. Capture real live-provider traces/results where access exists, with versions and timestamps. Maintain explicit offline fixtures and sanitized replays. Never present replay/fixture behavior as a successful live integration.
6. Preflight accounts, model/feature availability, privacy constraints, spending limits, integrations, browser access, workers and scheduler. Prefer official supported APIs; record beta/preview and deprecation status and freeze the demo versions.
7. Supply participant materials: request-flow map, glossary, setup, annotated code, scenario inputs, golden set, evaluation harness, reference patches, runbooks, source links, exercises and answer checks.
8. Verify product usability: first workflow understandable within a minute, no unrelated navigation/game rules, visible evidence and action status, clear failure/recovery, accessible browser flow.
9. Verify the teaching run: rehearse each timed contact; measure time; shorten live scope if over budget and retain the omitted depth in explicit reference/practice material.

## Participant outcomes and evidence

After the facilitated contacts, participants should be able to trace a request, explain trust/runtime boundaries, diagnose a demonstrated failure, interpret evaluations/traces, assess a Codex diff, and justify a pilot decision. Independent implementation proficiency is assessed through the optional practice, not attendance alone.

The practice acceptance pack covers: one grounded vertical slice; one permission/injection regression; a reviewed golden set and before/after experiment; a bounded tool/agent run; memory isolation/deletion; a scheduled durable approval workflow; a ticket-to-PR change with browser evidence; and an FDE discovery/pilot/handover memo. Advanced references add multi-agent, programmatic tools, realtime, and model adaptation without requiring every learner to deploy every framework.

## Official OpenAI documentation reviewed

These links support capability choices, not an assertion that all accounts expose every feature. Recheck before implementation and again before delivery.

- [API deployment checklist](https://developers.openai.com/api/docs/guides/deployment-checklist): runtime controls, tool workflows, caching, compaction, background execution and operational error handling.
- [Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk) and [Agents API](https://developers.openai.com/api/docs/guides/agents-api/overview): application-hosted versus managed agent execution. The managed API currently documents US-only residency and no ZDR support; validate suitability rather than assuming self-hosted compute changes service retention.
- [Scheduled tasks](https://learn.chatgpt.com/docs/automations?surface=app): current destination of the Codex app automation documentation; scheduling/events and skills have environment/account prerequisites.
- [Build skills](https://learn.chatgpt.com/docs/build-skills) and [API skills](https://developers.openai.com/api/docs/guides/tools-skills): reusable instructions/resources and runtime-specific distribution/attachment.
- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) and [non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode): programmatic integration and scripts/CI with explicit execution controls.
- [Webhooks](https://developers.openai.com/api/docs/guides/webhooks): signed events, prompt acknowledgement, retries and deduplication.
- [Background mode](https://developers.openai.com/api/docs/guides/background): asynchronous inference; assess temporary storage and cancellation behavior.
- [Data controls](https://developers.openai.com/api/docs/guides/your-data): endpoint-specific retention/residency eligibility; do not equate store=false with universal zero retention.
- [Agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals): trace grading, datasets and repeatable evaluation.
- [API skills/tool workflow index](https://developers.openai.com/api/docs/guides/tools-skills): tool search, programmatic and asynchronous calling belong in advanced references, subject to supported runtime/model.

Current documentation marks Agent Builder for deprecation/shutdown on 30 November 2026. Do not base a new course implementation on that surface. Teach transferable evaluation/model-adaptation concepts and recheck supported platform surfaces rather than assuming older fine-tuning/evaluation tutorials remain current.

## Next implementation planning work

The owner authorized the next implementation phase. Relay is selected, the product design/runbook/test plan have been rewritten together, and the local FastAPI baseline and isolated references have passed their recorded local checks. See `workbench/evidence/VERIFICATION.md` for actual outcomes. Remaining work includes account-dependent live preflight, reviewed evaluation data, advanced practice implementations and timed rehearsal. External integration writes and production deployment remain outside the authorized local work.
