# Relay documentation

Start with the [repository README](../README.md) for access links and local setup. The active product is Relay's Python/FastAPI support workbench; its baseline and opt-in teaching apps share the same source repository.

## Follow the course

- [Contact 1](teaching/CONTACT_1_PREPARATION.md): RAG, Responses, streaming and evaluation walkthrough.
- [Contact 2](teaching/CONTACT_2_REHEARSAL_GUIDE.md): the two-hour PDF and governed Codex session, with copyable prompts and code maps.
- [Contact 3 — Shoplytic](teaching/CONTACT_3_SHOPLYTIC.md): the 60-minute Codex SDLC demonstration, read-only MCP task, slide deck and rehearsal prompts.
- [Participant practice](teaching/RELAY_PRACTICE.md): exercises and expected evidence.
- [Checkpoints](CHECKPOINTS.md): repeat an exercise or inspect its completed implementation.

## Maintain the application and curriculum

| Document                                                            | Purpose                                                              |
| ------------------------------------------------------------------- | -------------------------------------------------------------------- |
| [Product and technical design](PRODUCT_AND_TECHNICAL_DESIGN.md)     | Product requirements, architecture and business/security invariants. |
| [Facilitator runbook](FACILITATOR_RUNBOOK.md)                       | The four-contact progression and recovery approach.                  |
| [Test and evidence plan](TEST_AND_EVIDENCE_PLAN.md)                 | What acceptance and verification need to prove.                      |
| [AI engineering/FDE blueprint](AI_ENGINEERING_AND_FDE_BLUEPRINT.md) | Breadth of the curriculum and practice mapping.                      |
| [Delivery roadmap](ISSUES.md)                                       | Remaining implementation and delivery work.                          |
| [Contact 1 coverage map](teaching/CONTACT_1_COVERAGE_AUDIT.md)      | Topic-to-code/evidence mapping and its limitations.                  |
| [Deployment](DEPLOYMENT.md)                                         | Render configuration, public limits and owner-controlled deploys.    |

Implementation commands live in [workbench guidance](../workbench/README.md). The single profile registry is [workbench/checkpoints.json](../workbench/checkpoints.json). [Evidence](../workbench/evidence/README.md) keeps the dated records used by the course; new screenshots, PDFs and test output go into ignored runtime folders.

Superseded plans, duplicate documents and old generated artifacts are recoverable from Git history. They are not additional requirements for the current app. Keep fixture, recorded and live results distinct, and preserve the baseline's intentional teaching limitation and the isolated exercises.
