# Verification evidence

This folder keeps a small, curated set of records used by the course. The records are dated observations, not a claim that every provider, model or deployment still behaves the same way.

| Record | What it supports |
| --- | --- |
| [Contact 2 release](contact2-release-verification.json) | The published PDF feature's local checks: 207 Python passes, 36 browser passes and the staged-upload regression fix. |
| [Page-reference preparation](contact2-page-reference-preparation.json) | Recorded before/reference acceptance results for the original coding exercise. |
| [PDF provider run](contact2-pdf-preparation.json) | A real-provider one-page PDF run, predating the later direct-query route. |
| [Codex preparation](contact2-preparation.json) | Recorded permission denial, cached-token usage, bounded repair and docs-MCP results from the Markdown task. |
| [Contact 1 live setup](contact1-live-setup-status.json) | Recorded OpenRouter, evaluation, comparison and trace results and their limitations. |
| [Contact 1 hybrid RAG smoke](contact1-clean-rag-live.json) | Two recorded real hybrid/streamed answers using disposable data. |
| [Langfuse receipt](contact1-langfuse-receipt.json) | The recorded collector receipt; read its scope before treating it as a model-run trace. |
| [Hosted container check](hosted-container-live.json) | A recorded container run, not proof of the current Render deployment. |

The six `desktop-contact2-pdf-*-fixture.png` and `mobile-contact2-pdf-*-fixture.png` images show page 2, spanning pages and metadata-free legacy sources. They are browser fixtures, not live model answers. `hosted-container-live.png` accompanies the recorded container check.

## Generate fresh results

From the repository root:

```sh
pnpm verify
```

- Browser screenshots and exported slide PDFs: `workbench/.runtime/browser-evidence/`.
- Deterministic evaluation JSON and Markdown: `workbench/.runtime/evaluation/`.
- Playwright failure traces: `test-results/relay/`.
- Source fingerprints: `workbench/checkpoint-files.json`, refreshed with `pnpm relay:verify --record-checkpoint` after deliberate changes pass verification.

These output folders are ignored by Git. Browser tests regenerate the Contact 1, concepts-only and Contact 2 PDF handouts; the web slides also have a Print / PDF control. Normal verification uses disposable stores and fixtures, not billable provider calls.

Older screenshots, PDF exports, logs and superseded reports remain in Git history, including the `contact-2-complete` checkpoint and pre-cleanup commit `9107c79`. Paths inside historical JSON records describe their original runs; they may refer to artifacts now kept only in that history. Preserve the original record rather than rewriting it as a new result.
