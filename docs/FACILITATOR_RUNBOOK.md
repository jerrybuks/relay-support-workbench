# Relay — facilitator runbook

Active replacement for the game runbook. Four contacts: Contacts 1, 3 and 4 are 60 minutes; Contact 2 is 120 minutes. Learners are technical; ordinary API engineering is prepared beforehand. Contacts 1–3 use approximately 15 minutes of slides plus 45 minutes of facilitator-led demonstration/engineering. Contact 4 uses evidence and decision exercises; participant presentations are not required.

Read the [coverage audit](teaching/CONTACT_1_COVERAGE_AUDIT.md), then [product/design](PRODUCT_AND_TECHNICAL_DESIGN.md), [test/evidence plan](TEST_AND_EVIDENCE_PLAN.md), [full coverage blueprint](AI_ENGINEERING_AND_FDE_BLUEPRINT.md) and the current verification report before teaching. A listed feature is not necessarily a completed reference. The checkpoint registry and evidence define what actually works.

## Rehearsal and preflight

1. Install locked dependencies and run the baseline, API tests, evaluation and browser checks. Start the user-facing app on loopback. Use a separate disposable database for each reference/contact; never reset the owner's working database.
2. Check the exact checkpoint/profile and provider on `/api/health`. Read the registry's verification status; a fixture result does not prove live model quality.
3. Open the late-delivery case, investigate, inspect evidence, propose ₦2,000, switch demo persona to supervisor and approve. A second browser is a separate workspace, so use the same browser to change personas.
4. Prepare the golden set, baseline/reference reports, known failing inputs, exact edits/reference diffs and recovery commands. Keep a sanitized replay if a provider is unavailable.
5. Preflight model/SDK access, spending limit, vector index, Langfuse, Temporal service, MCP server and intended ticket/repository integrations. Record which run live, locally, or as a replay. Missing access changes the disclosed mode; it must not be hidden.
6. Confirm all external writes and publication are separately authorized. Use fictional/local fixtures otherwise. Keep real credentials out of prompts, slides, logs and Git.
7. Run the timed rehearsal. Shorten live edits rather than omitting failure/recovery evidence. Supply annotated reference walkthroughs for the remaining breadth.

## Contact 1 — grounded application engineering

The [Contact 1 preparation guide](teaching/CONTACT_1_PREPARATION.md) supplies the main live RAG launch command and optional historical fixture commands, account preflight, evaluation and tracing boundaries, and the prepared reference walkthrough.

### Opening narrative — full rehearsal version

You've been brought in as an AI engineer at **Kora Dispatch**, a fictional Nigerian logistics company.

The team has used ChatGPT to explain ideas, write messages and solve problems. They're impressed, and now they're asking: **“Can we bring this capability into our own product to help our support agents?”**

Their support team is overwhelmed with customer questions about late deliveries, address changes and damaged parcels. Many of these questions are similar, but agents still have to look up each shipment, find the relevant policy and work out what they can offer the customer. As the queue grows, customers wait longer and agents have less time for complicated cases.

The team wants AI to help agents find the right information and prepare answers more quickly, while keeping people responsible for decisions that need approval.

Imagine one of those messages comes from a customer who asks:

**“I paid ₦8,000 for express delivery, but my parcel arrived two days late. What can you do about it?”**

A useful answer needs facts from the company. The AI must check when that parcel was delivered, which delivery service the customer paid for, and what the current company policy allows.

For example, the policy may allow the agent to recommend compensation of up to ₦2,000 for that delay. But a supervisor must approve the amount before the system records it. The AI cannot approve compensation itself or promise the customer a cash refund.

The company also needs the AI to respect access permissions. A support agent should only receive information they're allowed to see. Each answer should show which policy supports it. If the information is missing or the policies disagree, the AI should say so and explain what needs checking.

**Your assignment is to build this capability into Relay, Kora Dispatch's support workbench.**

The application and its APIs are already in place. Today, we'll connect the AI to company policies and shipment records, follow one customer question through the system, and check the answer before showing it to the support agent.

Then we'll test it: **does it find the right information, give a supported answer and stay within its permissions?** We'll also inspect how long it took and what it cost.

That's our job today: turn a capable model into a useful product feature that the company can evaluate and control.

_Facilitator note:_ This is the full narrative for rehearsal or pre-session context. For the scheduled 30-second opening, use the company setup, the customer's question and the assignment, then let the following slides introduce the details. “Compensation” here means the policy's delivery-fee credit; Relay records an approved amount in a local demonstration ledger. It does not execute a payment or refund.

### Prepare before class

- Working M0 workbench/API. Basic auth/role/tenant/CSRF/idempotency patterns available to inspect; local demo identity explicitly disclosed.
- Title-match baseline, FTS intermediate and prepared OpenAI-embedding/Qdrant RAG reference; synthetic policy corpus and versioned draft golden/held-out sets awaiting facilitator approval.
- Explicit billable embedding/index command, persistent Qdrant chunks, vector/hybrid comparison, Responses adapter, actual local-store/SDK transport tests and live evaluation command. Live model results require actual configured access and a separate report.
- Source/permission checks and adversarial cases; latency/usage fields with null values when unmeasured.
- Application-linked context, bounded agent and direct/LangGraph comparison paths; native/LangChain chunking choice. Prepare a selected live model/settings experiment and the bounded read-only Codex task.

### Presentation and navigation

For an explanation-only session, open the [separate concepts deck](http://127.0.0.1:8000/static/contact1-concepts.html). It contains the existing 15 concepts with spoken explanations, diagrams and code references, without demo cards, profile links, build directions or prescribed timings. The course page links to it as the main presentation. The timed deck below remains a separate teaching guide; creating this alternative does not change the four-contact curriculum budget.

The complete [Contact 1 web presentation](http://127.0.0.1:8000/course/contact-1) follows this runbook: 15 concept slides, five timed demo cards, ten appendix slides and notes for every slide. Open from `/course`; use **G** for contents and **N** for speaker notes. Print/PDF exports the participant deck without notes. The optional timer supports rehearsal; the schedule below remains the teaching budget. See the [preparation guide](teaching/CONTACT_1_PREPARATION.md#web-presentation) for controls and recovery.

### 0–15 minutes: slides

Business problem and success criteria; model versus agent harness (horse analogy); governance as rules, decision rights and accountability, translated into runtime/API/database controls; existing API; explicit OpenAI Responses request/output contract; trusted developer instructions versus evidence; tool/result loops; caller-managed history versus response chaining and Conversations; provider streaming versus Relay SSE; RAG, Langfuse and evaluation. Fifteen concept slides still end at minute 15. The opening case/outcomes take 30 seconds each; the horse/harness and governance/control slides take 45 seconds each; the request-path overview takes 30 seconds. Responses still starts at minute 3 and the live demonstration still starts at minute 15.

### 15–60 minutes: demonstration

| Minutes | Action                                                                                                                                                          | Evidence                                                                                            |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 15–23   | Stay in the live RAG app on port 8002. Open RY-1042, ask the compensation question, read the answer and open its cited policy.                                  | Real provider response, authorized source text and supervisor boundary.                             |
| 23–38   | Follow the same request: inspect query embedding + hybrid retrieval in Swagger, then Responses, shipment tool, streamed progress and validated completion.      | Source/version/offsets, explicit vector versus lexical scores, separate embedding/generation usage. |
| 38–48   | Request restricted/unsupported evidence and unauthorized action; demonstrate context/deletion; inspect provider-state comparison and cancellation/loop failures | Denial, no fabricated citation, safe service boundary                                               |
| 48–55   | Inspect live evaluation reports, nested trace, judge/human distinction, usage and supplied-price estimates.                                                     | Category outcomes, disclosed limitations and conditional pilot/no-go decision.                      |
| 55–60   | Codex explains the request path and proposes one narrowly scoped test                                                                                           | Controlled introductory interaction, no sprawling patch                                             |

Suggested Codex prompt: “Explain Relay's investigation path and identify where tenant permissions, source validation and credit authority are enforced. Do not edit files. Name one regression test for each boundary.”

The participant-visible [coverage audit](teaching/CONTACT_1_COVERAGE_AUDIT.md#participant-visible-audit--21-october-2026) is the teaching contract. The provider-state SDK comparison is separate from Relay case memory. Prepare a reviewed conflicting-policy case and actual model/settings comparison before claiming full demonstration readiness.

The main walkthrough uses one live RAG app; title-only and FTS fixtures are optional practice, not a required sequence. The 23–38-minute segment is an end-to-end code walkthrough rather than a title-to-FTS live edit. This keeps Contact 1 focused on the AI pipeline while retaining the baseline for isolated engineering exercises.

Follow-up reference: prompt/context versions, stateless/stateful strategies, caching/model comparisons, deeper hybrid tuning/reranking and deployment controls. These have guided exercises rather than extra live build time.

## Contact 2 — practical AI engineering with governed Codex

Contact 2 now has **120 minutes**, replacing the older 60-minute duplicate-event repair demonstration. Use the [Contact 2 rehearsal guide](teaching/CONTACT_2_REHEARSAL_GUIDE.md) for the talk track, code paths, task prompts, timing, recovery and readiness gates. This is the session-specific override to the original four-hour plan; if the other three contacts remain one hour, total facilitated time is five hours.

Begin with the working PDF upload demonstration in the policy lab: upload → inspect extracted text → inspect chunks → review/index → inspect actual embeddings/Qdrant records → ask and expand the source. Keep one page visible beside the code. The replacement Codex task adds original PDF page references to passages and citations. Its reference implementation still needs preparation; a three-page sample PDF is provided. Separately, the old Markdown parser exercise is no longer in the main session.

The task is to ingest an approved policy into a disposable Relay teaching workspace and verify its retrieval, answer and citation. Trace the existing pipeline first, then demonstrate prompting, `AGENTS.md`, two general engineering skills, a reusable ingestion skill, external documentation MCP, permissions, context, caching, browser verification and PR review through that one assignment.

Earlier technical preparation is recorded in `workbench/evidence/contact2-preparation.json`; the PDF run is in `workbench/evidence/contact2-pdf-preparation.json`. Those records do not verify the replacement page-reference exercise. Prepare that exercise and its PDF skill reuse before the timed rehearsal. Keep the older parser and duplicate-event fixtures as separate practice.

| Minutes | Action                                                                        |
| ------- | ----------------------------------------------------------------------------- |
| 0–5     | Introduce the business problem and engineering assignment                     |
| 5–30    | Demonstrate PDF ingestion, retrieval and a cited answer alongside the code    |
| 30–45   | Set up model/effort, prompting, Plan mode, repository context and permissions |
| 45–75   | Add PDF page references through a visible test/patch/feedback loop            |
| 75–90   | Demonstrate three skills and a read-only external MCP lookup                  |
| 90–110  | Verify the browser journey, review the diff and prepare a local PR draft      |
| 110–120 | Explain context/cache reuse, inspect prepared automation and take questions   |

The full review/publication lifecycle, source revocation, Temporal and scheduled automation remain in Contact 3. Local drafts and recorded results must not be presented as actual remote writes or live executions.

## Contact 3 — governed ingestion and durable automation

For the Shoplytic class, use the [Contact 3 Shoplytic guide](teaching/CONTACT_3_SHOPLYTIC.md) and its completed slide deck instead of the Relay exercise below. That 60-minute session follows a new engineer through research, planning, a bounded MCP change, testing, review and release preparation. The ingestion/Temporal sequence remains a separate exercise; it is not part of the Shoplytic demo.

### Prepare before class

Local valid/duplicate/missing-provenance/injection fixtures, ingestion candidate parser, reviewed publication boundary, unfinished skill/AGENTS exercise plus separate completed reference, Temporal approval workflow and scheduling definition, MCP tool scope and run-evaluation report. Temporal infrastructure is prepared, not installed during class.

| Minutes | Action                                                                                                            | Evidence                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 0–15    | Slides: skill/MCP/workflow distinctions, memory/state, ingestion governance, scheduling/events                    | Clear ownership and trust boundaries                              |
| 15–30   | Codex improves a bounded candidate-ingestion path using the skill; test malicious and incomplete inputs           | Candidate stays untrusted; duplicates and missing provenance fail |
| 30–40   | Review/publish authorized material in the reference; inspect freshness and isolation checks                       | Review record, versioned source, no unreviewed retrieval          |
| 40–52   | Trigger the prepared workflow immediately; wait for approval, interrupt/restart worker, resume and retry delivery | Durable state, approved exact action, one local effect            |
| 52–60   | Inspect full-run trace/evaluation and audit/PR artifacts; introduce optional practice                             | Task completion, permissions and cost assessed together           |

Explain local schedule versus application-owned schedule versus asynchronous inference. Inspect timezone, overlap, duplicate/missed events, pause/cancel and run history. Do not wait for a real future schedule during class. Expose multi-agent, advanced memory and realtime/multimodal references through annotated material and practice.

## Contact 4 — FDE delivery and readiness

| Minutes | Action                                                                                                | Evidence                                                              |
| ------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 0–10    | Revisit customer assumptions, workflow baseline, stakeholders and success metrics                     | Discovery brief; assumptions distinguished from research              |
| 10–25   | Decide pilot scope from quality/security/cost reports                                                 | Thresholds, dataset provenance, failure slices, open risks            |
| 25–40   | Incident/recovery exercise: stale source, revoked permission, duplicate event or interrupted approval | Containment, audit, recovery and rollback decision                    |
| 40–50   | Rollout/adoption/handover; compare advanced voice, multi-agent and model-adaptation options           | Named operator, support plan, measured outcomes and trade-offs        |
| 50–60   | Separate API and Codex certification-readiness reviews                                                | Individual gaps and follow-up plan; no learner presentations required |

## Breadth and participant practice

Every blueprint topic must have a named code/report/reference or exercise before delivery. “Mentioned on a slide” is orientation, not an implementation outcome. Four hours cannot establish independent mastery across the whole inventory.

Provide setup, glossary, request-flow diagram, annotated code, dataset/harness, reference patches and answer checks. Optional practice after Contact 3: grounded vertical slice, injection/permission regression, measured evaluation, bounded tool loop, memory isolation/deletion, scheduled durable approval, ticket-to-PR/browser evidence and FDE pilot/handover memo. Include extensions for multimodal/realtime, multi-agent and model adaptation.

## Contingencies and evidence

- API unavailable: use disclosed fixture mode; do not claim live factual quality, tokens or cost.
- Temporal unavailable: use deterministic workflow tests and recorded replay; mark worker-restart/schedule proof unavailable until actually run.
- MCP/ticket/cloud unavailable: local read-only fixture and captured reference; no fabricated remote success.
- Time pressure: use verified intermediate/reference state, show exact diff and preserve the evaluation/release decision.

Save sanitized inputs, expected/actual results, provider mode, versions, test/evaluation outputs, browser evidence, reviewed diff and decisions per contact. Never include raw keys or private reasoning. Registry entries remain pending until their stated checks have passed.

### OpenRouter delivery adjustment

For the OpenRouter-funded rehearsal, use the provider configuration in [Contact 1 preparation](teaching/CONTACT_1_PREPARATION.md#openrouter-billing-route). Responses, embeddings/RAG, tools, caller-managed context and streaming keep their existing demo slots, subject to live preflight. Explain the gateway route visibly. Native stored response chaining and Conversations remain SDK/reference walkthroughs until funded direct OpenAI access is available; do not present them as live OpenRouter capabilities. Preserve the four-hour schedule and keep the existing zero-key recovery profile. Gateway mock tests and Langfuse metadata receipt are not proof of a live generated-answer run.
