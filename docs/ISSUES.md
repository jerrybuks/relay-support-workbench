# Delivery roadmap

The working application and course entrypoints are listed in [the checkpoint registry](../workbench/checkpoints.json). [Recorded evidence](../workbench/evidence/README.md) explains what was checked. This is the remaining delivery work, not a second source of product requirements.

## Implemented foundation

- FastAPI baseline with isolated demo identities, policy/tenant checks, reviewed credit proposals, transactional idempotency and a zero-key fixture assistant.
- Contact 1 opt-in embeddings/Qdrant/Responses runtime, caller-managed context, bounded tools, streaming, evaluation and observability references.
- Contact 2 PDF ingestion/querying, page-reference before/completed checkpoints, slides, repository skills and offline regression/browser checks.
- Contact 3 candidate-review and Temporal examples remain separate references. A tested example does not establish the complete application workflow.

Architecture and invariants live in [the product design](PRODUCT_AND_TECHNICAL_DESIGN.md); session sequencing lives in [the runbook](FACILITATOR_RUNBOOK.md). Completed implementation notes and older plans are available in Git history.

## Remaining work

| ID         | Area                                | Acceptance                                                                                                                                                          |
| ---------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DATA-01    | Policy and evaluation-set review    | Record reviewer/provenance, held-out cases and risk-based thresholds. Synthetic draft data is not customer acceptance.                                              |
| RAG-01     | Retrieval and answer quality        | Compare the same questions/corpus; measure semantic support, abstention, latency and usage. Treat reranking as an evaluated extension.                              |
| OBS-01     | Operational trace review            | Recheck the configured collector, redaction and model/prompt/corpus linkage. Earlier recorded receipts are retained.                                                |
| CLOUD-01   | Ticket and Codex cloud integrations | Record authorized real runs or clearly labelled replay. Local CLI and GitHub CI already have evidence; they do not prove ticket-platform integration.               |
| INGEST-01  | Governed publication                | Connect candidate review/version replacement to the application. PDF ingestion and physical page provenance are already covered in Contact 2; OCR is separate work. |
| DURABLE-01 | Durable business effects            | Connect authenticated approval to the app ledger, prove worker recovery/exactly one effect, and perform an actual source-version freshness check.                   |
| LABS-01    | Selected advanced practice          | Give memory, multimodal/realtime, multi-agent and optimization exercises repeatable acceptance checks before advertising them as implementations.                   |
| FDE-01     | Pilot and operations                | Validate customer assumptions, owners, retention, rollout/rollback and readiness criteria.                                                                          |
| SESSION-01 | Remaining teaching preparation      | Keep Contacts 3–4 materials, account preflights and session timing aligned with the implemented scope.                                                              |

Provider credentials, real integrations and production readiness have their own gates. Ordinary local verification does not authorize external writes or certify semantic quality.
