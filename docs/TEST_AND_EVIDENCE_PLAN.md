# Relay — test and evidence plan

Scope: local workbench baseline and separately verified teaching references. Superseded game evidence is available only in historical Git tags. Use the current Relay checks and evidence for this product.

## Baseline acceptance

- A new browser gets three synthetic cases; another tenant's case/policy never appears. A second browser is isolated from the first workspace.
- The late-delivery workflow completes: investigate → inspect canonical policy and shipment facts → propose no more than ₦2,000 → supervisor review → resolved case and one ledger credit.
- Address/damage cases show appropriate guidance and cannot receive an ineligible delay credit.
- Saved exchanges survive reload, can be omitted or deleted, and remain scoped to the case/workspace. This does not prove model memory or semantic recall.
- Observer cannot mutate cases, query the assistant or erase history. Agent cannot approve. Client-supplied role/tenant fields fail validation.
- Proposal amount/eligibility/version are checked server-side. Stale or changed idempotent requests fail. Concurrent identical approval retries produce one credit.
- Cookie/session rotation, expiry, hashed-at-rest tokens, CSRF/origin restrictions, body/field/rate limits and stable redacted errors are verified.
- Browser source/evidence escape untrusted strings. CSP disallows inline/eval/third-party execution. Interactive OpenAPI assets work offline.
- Full workflow passes in desktop and narrow mobile browser views, including keyboard focus/dialog behavior, knowledge/activity navigation and a clear next action.
- Production startup fails closed because real identity/deployment controls are not configured.

## Reference acceptance

| Contact | Required local proof                                                                                                                                      | Additional account/infrastructure proof                                                                                                   |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | Same fixed dataset compared across baseline/retrieval reference; source ACL and canonicalization; fake-transport Responses schema/refusal/citation checks | Real embedding/answer provider smoke, calibrated retrieval/answer quality, latency/usage and Langfuse collector delivery when provisioned |
| 2       | Reproducible red fixture, corrected reference green, retry/concurrency checks, local ticket and reviewed diff/PR draft                                    | Actual Linear/GitHub/cloud actions only when configured/authorized; otherwise clearly disclosed replay                                    |
| 3       | Candidate validation/injection/provenance/duplicates, skill/reference checks, bounded MCP call, workflow state/idempotency tests                          | Real Temporal worker stop/resume and schedule run; real integrations when configured; never equate unit tests with durability proof       |
| 4       | Sanitized incident inputs, reasoned go/conditional/no-go decision, rollback/handover checklist and practice rubric                                        | Customer stakeholder acceptance and real operational evidence before any production claim                                                 |

## Evaluation design

Create a versioned draft golden set from original synthetic policies. Include exact title, paraphrase, no-source, conflicting/outdated candidate, restricted source, foreign tenant, prompt injection, tool failure and ineligible shipment cases. A facilitator/domain reviewer must approve the set before treating it as gold-standard customer evidence.

Separate retrieval/source correctness, response schema, citation support, task completion, unauthorized actions and refusal/fallback outcomes. Compare the same inputs and corpus versions. Do not score a deterministic excerpt template as live model factual accuracy. The local report records fixture provider, no model, zero live API spend, and null unmeasured token/latency statistics. The intermediate wording/tag improvements are not an embedding benchmark. The completed RAG reference executes actual local Qdrant and actual SDK transport tests using mock embedding vectors; this proves persistence, ranking/filtering, cache/freshness and pipeline contracts, not live semantic quality. Live evaluation records source recall@k/MRR, embedding and Responses usage separately. Calibrate the draft cosine threshold using reviewed held-out cases. Reranking is not implemented.

For live evaluation, add held-out data, repeated runs, human-calibrated judges and slice reports. Report denominator, failures and limits. Select release thresholds using customer risk and measured baselines; do not invent production readiness from a passing smoke test.

## Evidence format

Each verification bundle records: date; source revision/content fingerprint; dependency lock; commands and exit codes; checkpoint/provider; dataset/corpus/prompt versions; actual results; browser screenshots; unavailable checks; and open risks. Fixture/replay/live modes must be unmistakable.

Never store credentials, raw customer data or chain-of-thought. Traces may include source IDs, tool names, validated non-sensitive arguments, policy decisions, timings and model usage when measured. Audit retention differs from deletable conversation history and must be explained.

## Test commands and reset policy

See README and `workbench/README.md` for current commands. Tests use temporary SQLite files. Browser QA uses its own database and loopback port. No command globally resets the user-facing app. A fresh demo workspace can be obtained in a new browser context. A reset helper, if added later, must target a known disposable file explicitly.

Fail CI for failed assertions, schema/format violations, false checkpoint claims or unreviewed baseline/reference imports. External service tests are opt-in and must report skipped/unavailable states rather than silent success. Dependency and secret checks supplement tests; they are not proof that every vulnerability is absent.

The integrated Contact 1 reference additionally exercises the actual OpenAI SDK through an HTTP mock at the FastAPI boundary: tool budget/scope, schema/canonical citations, timeout/incomplete/refusal failure, role-scoped persistence, profile cookie isolation and telemetry failure. Browser checks cover guided progress, readable run records and unsaved preview separation. `pnpm contact1:eval:live` is a separate opt-in billable harness with an attempt budget and pending human semantic-review fields; ordinary verification makes no provider calls. See [Contact 1 preparation](teaching/CONTACT_1_PREPARATION.md).

The Contact 1 runtime audit adds integration proof for opt-in case context, current-source revalidation and deletion, bounded agent loops, the actual LangGraph path, the actual LangChain chunker in Qdrant indexing, SDK SSE parsing, early disconnect without partial persistence, nested actual Langfuse SDK observations using a local exporter, explicit model controls, judge budgets/verdict consistency, generated-run-bound human labels and cached/embedding token-cost arithmetic from supplied test rates. Browser presentation fixtures verify reference options and streamed-result rendering; they do not establish live provider quality. Ordinary verification still makes no OpenAI/hosted Langfuse calls. The [coverage audit](teaching/CONTACT_1_COVERAGE_AUDIT.md) lists later-contact gaps instead of treating them as credential-only prerequisites.
