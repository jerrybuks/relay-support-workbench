# Relay checkpoints

[workbench/checkpoints.json](../workbench/checkpoints.json) is the single execution-profile registry. The public repository contains Relay; superseded products are not part of its current source.

| Source               | Use                                                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `main`               | Current completed application, fixes, slides and repository skills.                                                     |
| `contact-2-before`   | Original PDF app before the page-reference exercise; its explicit page-reference acceptance has five expected failures. |
| `contact-2-complete` | Published completed Contact 2 feature. Later fixes and documentation continue on `main`.                                |

A tag selects source, not the running profile. `pnpm dev` starts the zero-key baseline. `pnpm contact1:live` starts the opt-in case/RAG runtime. `pnpm contact2:before` starts the PDF teaching app; its `before` flag controls the separate Markdown exercise and does not remove page references from completed source.

To repeat Contact 2 without disturbing an existing checkout, follow [the session guide](teaching/CONTACT_2_REHEARSAL_GUIDE.md). Use independent runtime stores and browser contexts. Never reset an existing working tree, delete owner data or move published tags just to recreate a starting point.

The baseline's intentional title-retrieval limitation, the optional unfinished Markdown parser and the separate idempotency practice remain available. Contacts 3–4 have their own references and preparation boundaries in the registry and [runbook](FACILITATOR_RUNBOOK.md).

[Recorded evidence](../workbench/evidence/README.md) distinguishes local tests, historical provider runs and unverified quality/operational claims. Source hashes in `workbench/checkpoint-files.json` detect drift; they do not replace running the relevant checks.
