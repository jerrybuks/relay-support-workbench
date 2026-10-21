# Relay implementation plan — 20 October 2026

## Product and teaching decision

The active product is Relay, a fictional logistics support-resolution workbench with a FastAPI backend. The owner authorized the expanded [AI engineering/FDE blueprint](AI_ENGINEERING_AND_FDE_BLUEPRINT.md). The previous game and its documents are preserved in historical Git tags; its source, dependencies and duplicate documents have been removed from the working tree.

The baseline must be usable without model keys and retain meaningful live engineering work. The default entrypoint must not import later teaching references. Account-dependent services and production deployment are separate readiness gates.

## Phases, deliverables and acceptance

| Phase                  | Deliverable                                                                                                                                       | Acceptance and current boundary                                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| P0: align              | Product/design, runbook, testing plan, coverage matrix and four-hour allocation                                                                   | Rewritten together; broader practice separated from live time; customer assumptions disclosed                                                  |
| P1: baseline           | FastAPI/OpenAPI, isolated local demo identities, queue, policies, fixture investigation, proposals/review, ledger and audit                       | Complete desktop/mobile workflow; policy/role/tenant checks, persistence, CSRF and concurrent idempotency pass                                 |
| P2: C1 reference       | Opt-in embedding/Qdrant/Responses RAG reference, lexical intermediate, bounded live evaluation and optional metadata export                       | Integrated actual-SDK HTTP-mock contracts verified; before/intermediate fixture comparison; credentialed live quality/usage remains unmeasured |
| P3: C2 reference       | Isolated intentional duplicate-event defect, regression, correction, MCP ticket and issue/PR task                                                 | Before intentionally red and reference green; actual MCP allowed/denied protocol calls; no real ticket write                                   |
| P4: C3 reference       | Candidate parser/review API, packaged skill, graph/chunking example and durable approval/schedule references                                      | Candidate/rights/duplicate tests; roles before publication; actual local Temporal worker recovery; schedule test status in evidence            |
| P5: delivery readiness | Independent reference registry, verification bundle, slides/practice and preflight list                                                           | Local evidence and limitations recorded; live integrations, full rehearsal and customer/corpus review remain prerequisites                     |
| P6: advanced practice  | Reranking/query rewriting, richer memory, multi-agent, realtime/multimodal, optimization/model adaptation, Codex CI/cloud and Windsurf comparison | Named exercises with acceptance evidence; not silently advertised as completed implementations                                                 |

## Architecture decisions

- FastAPI is a separate Python package under `workbench`; static same-origin frontend avoids unnecessary second-server/auth overhead. Historical Git tags preserve the old implementation without installing its dependencies.
- Use uv's exact dependency lock and Python 3.12 reference runtime. Optional SDKs do not run on default app startup.
- Local opaque cookie sessions and persona switching are an explicit development identity adapter. Production startup fails closed; real OIDC/SSO is not pretended implemented.
- SQLite uses schema versioning, WAL, parameterized SQL and transactions. Scope saved context and traces by role as well as workspace. Existing messages are conservatively restricted during migration.
- Backend eligibility and approval control credits. Models/skills can advise; they cannot authorize. The local ledger proves idempotency, not an external payment integration.
- Synthetic policies permit safe local fixtures without inventing historical facts, real customer rights or human approvals. The evaluation set is a draft until facilitator review.
- References are isolated modules and independent launch profiles/databases. The registry states that profile selection is explicit; checking out one revision alone does not automatically select a reference.

The [coverage audit](teaching/CONTACT_1_COVERAGE_AUDIT.md) corrects the earlier under-scoped reference and records remaining Contact 2–3 implementation work. Contact 1 now has runnable before/intermediate/live profiles with separate databases and cookies, a clearer case workflow, readable run records, a bounded billable evaluation command and a timed [preparation guide](teaching/CONTACT_1_PREPARATION.md). Baseline retrieval and Contact 2–3 exercises remain isolated.

## Outstanding delivery gates

Configure and actually measure authorized OpenAI/model/vector access and Langfuse export; preflight real Codex/Linear/GitHub/cloud capabilities; review dataset/corpus and participant course objectives; implement/verify chosen advanced labs; rehearse every timed contact; validate pilot identity/storage/retention/operations with customer owners. No external writes or public deployment are part of this local build.

Current results and exact verification commands belong in `workbench/evidence/VERIFICATION.md`. Do not treat plans, installed SDKs, mocks or schedule definitions as evidence of unavailable live behavior.
