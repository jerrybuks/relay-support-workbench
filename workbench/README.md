# Workbench development

Run commands from the repository root. The [main README](../README.md) explains learner access and setup; [docs/README.md](../docs/README.md) indexes the curriculum and design.

## Choose the app

| App                             | Command                | Default address                          |
| ------------------------------- | ---------------------- | ---------------------------------------- |
| Zero-key baseline               | `pnpm dev`             | http://127.0.0.1:8000                    |
| Contact 1 live case/RAG runtime | `pnpm contact1:live`   | http://127.0.0.1:8002                    |
| Contact 2 PDF assistant         | `pnpm contact2:before` | http://127.0.0.1:8002/teaching/contact-2 |

Only run one app on 8002. Use the [Contact 1 guide](../docs/teaching/CONTACT_1_PREPARATION.md) for explicit environment loading and index preparation, or the [Contact 2 guide](../docs/teaching/CONTACT_2_REHEARSAL_GUIDE.md) for PDF setup and the before/completed exercise.

`pnpm contact2:before` loads the ignored `workbench/.env`. Its state flag selects the separate Markdown parser; the PDF page-reference feature is already complete on `main`. The [checkpoint registry](checkpoints.json) records the entrypoints and stores.

## Install and verify

```sh
pnpm install --frozen-lockfile
uv sync --project workbench --locked --extra references
pnpm exec playwright install chromium
pnpm verify
```

Verification uses disposable stores and fixture provider responses. It runs Python/browser tests, formatting, source-reference checks, deterministic evaluation, secret scanning, packaging and baseline-import isolation. Optional real Temporal checks use `RELAY_TEMPORAL_TEST=1`; live model requests require separate explicit opt-in.

New screenshots and slide PDF exports go to `.runtime/browser-evidence/`; deterministic evaluation goes to `.runtime/evaluation/`. Both are ignored by Git. [Curated evidence](evidence/README.md) retains selected dated records. After deliberate code changes pass verification, `pnpm relay:verify --record-checkpoint` refreshes the tracked source fingerprint manifest.

## Code map

- `src/relay/`: baseline API, business rules, SQLite store and synthetic cases.
- `src/relay/static/`: buildless UI, course pages, slides and locally served Swagger assets.
- `teaching/contact2/indexing/pipeline.py`: PDF preview and chunk → embed → store coordination.
- `teaching/contact2/querying/pipeline.py`: retrieve → generate → validate coordination.
- `teaching/contact2/document_service.py`: upload/review/removal; `policy_store.py`: canonical source publication.
- `teaching/investigation_reference.py`: Contact 1 case tools, memory/runtime options and streaming adapters.
- `tests/`, `browser/`, `evals/`: assertions, visible journeys and draft evaluation inputs.
- `scripts/`: profile launch, preflight, evaluation and verification commands.
- `../.agents/skills/`: the single installed copy of each repository skill.

The baseline never imports teaching modules. `rag_reference.py` retains compatibility imports for Contact 1; the shared implementation lives in `contact2/indexing/` and `contact2/querying/`. The [reference module guide](teaching/README.md) covers the optional examples.

## Storage, providers and boundaries

The baseline database defaults to `.runtime/relay.sqlite`; override `RELAY_DB` with a disposable path for QA. Teaching profiles use their own SQLite/Qdrant stores. Never share an open local Qdrant index between a server and an indexing process.

The live references use OpenAI SDK embeddings and Responses, either directly or through the OpenRouter route configured in the environment example. OpenRouter caller-managed history is supported; native OpenAI stored-response/conversation demonstrations remain a separate reference. Local Qdrant needs no service credential. Model requests consume provider credits; installed dependencies alone do not activate them.

The PDF assistant accepts text PDFs up to 2 MiB, ten pages and 50,000 extracted characters. Preview is offline. Review and billable confirmation precede indexing. Questions use one ordinary JSON request to `POST /api/v1/policies/query`; this path does not stream. Canonical offsets supply page references, and citations retain similarity/ranking scores. Old indexed PDFs need explicit removal and re-upload to capture page metadata; the database is not automatically reset.

Demo personas are not production authentication. Tenant/role checks, CSRF, source review, approval and idempotency remain server enforced. Hosted workshop configuration, shared limits and ephemeral data are documented in [deployment](../docs/DEPLOYMENT.md); normal startup is loopback-only and production mode fails closed.

## Swagger maintenance

`/docs` serves the local Swagger UI against `/openapi.json`. Start **POST /api/v1/demo/session** or open the UI first. Try-it-out uses the session cookie and a fresh CSRF token; credit operations support explicit idempotency keys.

Vendored Swagger assets and their Apache-2.0 license/provenance are under `src/relay/static/vendor/swagger-ui/`. They work offline and remain outside formatting. For an upgrade, pin the official distribution, verify its integrity, preserve licenses/provenance and run the asset/packaging tests. Only the docs page allows the inline style attributes Swagger needs; application script security remains unchanged.
