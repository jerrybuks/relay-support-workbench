# Relay workbench

Run from the repository root:

```sh
uv sync --project workbench --locked
uv run --project workbench python -m relay.main
```

UI: http://127.0.0.1:8000 · API: http://127.0.0.1:8000/docs · schema: `/openapi.json`.

Course overview: http://127.0.0.1:8000/course. The participant-facing write-up follows the approved four-contact runbook and expanded blueprint, with core demonstrations separated from reference walkthroughs and guided practice. It introduces the project, audience, outcomes, session coverage and expected practice evidence. The info button after the project introduction opens the agreed Kora Dispatch context in a keyboard-accessible context dialog. The Contact 1 presentation is at http://127.0.0.1:8000/course/contact-1: 15 concept slides, five timed demo cards and ten appendix slides, with keyboard controls, conversational speaker notes written as a read-aloud talk track, a rehearsal timer and print-to-PDF. Relevant slides include copyable source-file/line footnotes; verification checks their locations against the Python definitions.

The separate [concepts-only presentation](http://127.0.0.1:8000/static/contact1-concepts.html) has 15 explanation slides with conversational notes and code references. It contains no demo cards, profile links, build instructions or prescribed slide timings. It is available as an optional concepts-only alternative. The original timed presentation and demo guide remain separately accessible. Both decks use the same local navigation/styles, and source-location verification covers both.

The default database is `workbench/.runtime/relay.sqlite`, excluded from Git. Override `RELAY_DB` with a disposable path for QA. The server binds loopback. Default `RELAY_ENV=local` is loopback-only. The separate hosted entrypoint supports explicit `RELAY_ENV=workshop` with a configured HTTPS origin, secure cookies and shared AI limits. No real login provider is configured. See [deployment](../docs/DEPLOYMENT.md).

## Swagger UI

`/docs` serves Swagger UI against FastAPI's `/openapi.json`. Start a local identity with **POST /api/v1/demo/session** in Swagger, or open Relay first. “Try it out” uses the current HttpOnly session cookie and fetches a fresh CSRF token for mutations, including after persona changes. Credit requests generate an idempotency key if the field is empty; enter/reuse a specific key to test retries.

Swagger UI **5.34.0** is served locally; there is no CDN or online validator dependency. Scripts remain external and restricted to the same origin. Only the docs page permits the inline style attributes used by Swagger; the workbench/API CSP stays strict. Assets and Apache-2.0 notices are under `src/relay/static/vendor/swagger-ui`, with source URL, npm package SHA-512 integrity and per-file SHA-256 values in `provenance.json`. No Node install/build is needed to serve the docs.

For an upgrade, select a pinned official `swagger-ui-dist` release, verify its npm tarball integrity, copy the bundle/CSS and both license files unchanged, update the provenance record, and run `pnpm verify`. Vendored bytes are excluded from formatting; tests check their recorded hashes and that the wheel contains the assets. See [FastAPI self-hosting guidance](https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/) and [Swagger UI configuration](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/).

## Structure

- `src/relay/`: baseline API, services, SQLite store, fixtures and static frontend.
- `tests/`: baseline and separately scoped reference checks.
- `teaching/`: opt-in contact/reference implementations; never imported by baseline startup.
- `scripts/`: fixture evaluation and verification helpers.
- `evals/`: original synthetic draft dataset; human review remains required.
- `evidence/`: reproducible results, limitations and browser artifacts.

## Baseline verification

```sh
uv run --project workbench --locked --extra references pytest -c workbench/pyproject.toml
uv run --project workbench ruff check workbench
uv run --project workbench python workbench/scripts/evaluate.py
pnpm exec playwright test --config workbench/playwright.config.ts
```

Playwright uses its own loopback server/database, desktop and mobile contexts. Browser dependencies are supplied by the root locked pnpm project. Install Chromium with `pnpm exec playwright install chromium` if absent. Do not delete the user-facing database to run tests.

## Teaching references

Install extra SDKs: `uv sync --project workbench --locked --extra references`. Reference modules are loaded explicitly and use their own database/profile. See `teaching/README.md` and the checkpoint registry for exact commands and actual verification status. A reference is not class-ready until its required checks pass; live credentials/infrastructure must be preflighted separately.

### Contact 1 RAG reference

After configuring ignored local credentials, explicitly build document embeddings with `pnpm contact1:index`, then start `pnpm contact1:live` on port 8002. The reference uses OpenAI embeddings and real persistent local Qdrant, followed by bounded Responses tools/structured output. Query embeddings and answer generation require credentials for the selected billing route: direct OpenAI, or OpenAI models through OpenRouter. Set `RELAY_AI_PROVIDER=openrouter` and `OPENROUTER_API_KEY` for the latter; see the preparation guide for model IDs and native-state limitations. Qdrant local mode needs no hosted account. Stop the live process before rebuilding the index. The main demo stays in this live app; the zero-key baseline and FTS intermediate remain separate optional exercises. Live retrieval defaults to hybrid vector + keyword ranking, with conservative missing-letter correction against permitted policy vocabulary. Set `RELAY_RETRIEVAL_MODE=vector` for an explicit comparison.

See [Contact 1 preparation](../docs/teaching/CONTACT_1_PREPARATION.md) for `uv --env-file` commands, vector/hybrid comparison, index lifecycle, scopes, usage budgets and live evaluation. `/api/v1/rag/status` and protected `/api/v1/rag/search` appear in the live profile's Swagger UI. No live provider quality or hosted Langfuse delivery is implied by the SDK-mock tests.

The live policy assistant shows a question, answer and expandable sources, with a single composer below. Four compact question cards sit underneath, tailored to the selected case; clicking one fills the composer for review before sending. Its **Inspect AI** button opens a separate keyboard-accessible panel: **Run details** shows usage/stages and source provenance, **Settings** holds context/workflow/agent/direct/LangGraph choices and saved-history options, and **Raw JSON** shows the execution record. Teaching controls and raw traces are absent from the main conversation. Validated streaming and approval authority are unchanged. `pnpm contact1:preflight` inspects readiness without network calls; `--live` explicitly runs a bounded provider smoke. Semantic judges, human review import, repeat/slice reports and supplied-price cost estimates are part of the evaluation harness. See the [coverage audit](../docs/teaching/CONTACT_1_COVERAGE_AUDIT.md) for the earlier omissions and later-contact implementation gaps; a listed SDK/topic is not a completed demo.

## Security and evidence limits

The local demo persona selector is not production authentication. Startup refuses production mode. Fixture answers are not generated by a model; title-only retrieval is intentionally incomplete. The server still enforces permissions and policy authority independently. There is no public deployment, external ticket write, payment or active recurring schedule.

The deterministic fixture extracts canonical evidence and reads authorized shipment data. “Saved exchange” means persisted history, not model memory. The baseline SSE endpoint transports a completed fixture result. The live reference has a separate actual-provider stream with progress events and a validated final result. See the [product design](../docs/PRODUCT_AND_TECHNICAL_DESIGN.md) and [test plan](../docs/TEST_AND_EVIDENCE_PLAN.md) for production gaps and acceptance criteria.
