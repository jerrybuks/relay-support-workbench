---
name: ingest-approved-policy
description: Preview and ingest a packaged approved Markdown policy into Relay's isolated Contact 2 corpus, then verify canonical storage, retrieval and citations.
---

Read `workbench/teaching/contact2/TASK.md`. Required inputs are the packaged document name, teaching state (`before` for the live exercise or `reference` for recovery), and isolated Contact 2 data directory. Never use the owner's Contact 1 database/index or the hosted service.

1. Preview with `workbench/scripts/contact2.py preview --document NAME --state STATE` through the locked project environment. Inspect metadata, separate approval match, exact chunks and offsets. Stop on rejection; do not edit approval records to force acceptance.
2. Confirm authorization for the billable import. The local lab also requires a supervisor demo persona. A skill cannot grant approval or bypass permissions.
3. Prefer the running teaching app's `POST /api/v1/teaching/policies` via its lab/Swagger, with preview first and then explicit billable confirmation. This runs under the app's index lock. If using the CLI `ingest --confirm-billable`, stop the app owning the index first; restart it afterward.
4. Inspect import source/version, new embedding calls and reused chunks. Repeating an unchanged import must add no duplicate and make zero new embedding calls.
5. Check permitted retrieval and the cited answer for the prepared question. Verify a restricted source remains unavailable to a support agent. Report actual input, source/version, mode, usage and checks; a successful import is not proof of semantic answer quality.

Reuse the existing pipeline. Do not duplicate its Python code in this skill. Stop for credentials, provider failures, incompatible settings or missing approval. Do not upload external source material, change policies, publish remotely or deploy.
