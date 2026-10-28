# Relay — Resolution desk

An API-first support workbench for a fictional Nigerian logistics company, and a practical project for four OpenAI API / Codex / AI engineering and FDE contacts.

Open a case, investigate shipment and policy evidence, propose a service credit, and review it as a supervisor. The M0 assistant is deterministic and clearly labeled; it needs no OpenAI key. No real messages or payments are sent.

## Open the course online

No local setup is needed to read the materials or explore the hosted workbench.

| Material                             | Link                                                                               |
| ------------------------------------ | ---------------------------------------------------------------------------------- |
| Course homepage and learning path    | [Open the course](https://relay-workshop.onrender.com/)                            |
| Contact 1 slides and speaker notes   | [Contact 1](https://relay-workshop.onrender.com/course/contact-1)                  |
| Contact 1 concepts-only slides       | [Concepts deck](https://relay-workshop.onrender.com/static/contact1-concepts.html) |
| Contact 2 slides and speaker notes   | [Contact 2](https://relay-workshop.onrender.com/course/contact-2)                  |
| Contact 3 slides and speaker notes   | [Contact 3](https://relay-workshop.onrender.com/static/contact3.html)              |
| Contact 4 slides and speaker notes   | [Contact 4](https://relay-workshop.onrender.com/course/contact-4)                  |
| Resolution desk and policy assistant | [Open the workbench](https://relay-workshop.onrender.com/dashboard)                |
| Interactive API documentation        | [Swagger](https://relay-workshop.onrender.com/docs)                                |

The hosted AI has shared request limits. The **Contact 2 PDF upload lab runs locally**; its code, sample PDFs and setup are below. The hosted site provides its slides.

## Run locally

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --project workbench --locked
uv run --project workbench python -m relay.main
```

Open the workbench at **http://127.0.0.1:8000/dashboard**. Interactive API documentation: **http://127.0.0.1:8000/docs**.

Course homepage and four-contact learning path: **http://127.0.0.1:8000/** (also available at `/course`).

Contact 1 presentation, speaker notes and demo guide: **http://127.0.0.1:8000/course/contact-1**.

Contact 3 slides: **http://127.0.0.1:8000/static/contact3.html**. Contact 4 slides: **http://127.0.0.1:8000/course/contact-4**.

The browser starts an isolated local demo workspace as Tolu, a support agent. Open RY-1042, choose **Investigate case**, inspect policy evidence, then **Propose a service credit**. Use **Demo persona** to switch to Amara and review it. Reload preserves the workspace. Another browser/context starts independently.

## Contact 2: code and slides from class

[Open the hosted Contact 2 slides](https://relay-workshop.onrender.com/course/contact-2). The current `main` branch includes the completed PDF page-reference feature, ingestion/query pipeline, offline tests and three repository skills under `.agents/skills/`.

To run the PDF assistant locally:

```sh
pnpm install --frozen-lockfile
uv sync --project workbench --locked --extra references
cp workbench/.env.example workbench/.env
```

Edit `workbench/.env` locally with your funded provider credentials and the configuration described in [workbench guidance](workbench/README.md). Never commit it. Then run:

```sh
pnpm contact2:before
```

Open **http://127.0.0.1:8002/teaching/contact-2** for the PDF assistant and **http://127.0.0.1:8002/course/contact-2** for slides. Upload one of the supplied synthetic PDFs, review its extracted text and confirm indexing before asking a question. Embedding and answer requests consume provider credits. The `before` command name selects the separate, intentionally unfinished Markdown practice; the PDF feature on `main` is complete.

Use tag **`contact-2-before`** in a separate checkout to repeat the original page-number exercise. Tag **`contact-2-complete`** identifies this completed release. Keep each checkout's runtime data separate. The [Contact 2 session guide](docs/teaching/CONTACT_2_REHEARSAL_GUIDE.md) includes the session goals, demo steps, prompts and verification commands.

The hosted service provides the course, slides and resolution desk. The PDF upload lab is a local opt-in teaching app; it is not enabled on the public service.

## Host the workshop

[Deploy the frontend and backend together on Render Free](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fjerrybuks%2Frelay-support-workbench). Supply your OpenRouter key through Render, not Git. The UI and AI are public with shared request limits. Free-instance restarts erase workshop history and rebuild the synthetic vector index. See the [deployment guide](docs/DEPLOYMENT.md) for the owner setup, limits and verification.

## Verify

Install the browser/formatting tooling with `pnpm install --frozen-lockfile` and the reference SDKs with `uv sync --project workbench --locked --extra references`.

```sh
uv run --project workbench --locked --extra references pytest -c workbench/pyproject.toml
uv run --project workbench ruff check workbench
uv run --project workbench python workbench/scripts/evaluate.py
pnpm exec playwright test --config workbench/playwright.config.ts
```

Detailed commands are in [workbench guidance](workbench/README.md). The [Contact 1 guide](docs/teaching/CONTACT_1_PREPARATION.md) and [Contact 2 guide](docs/teaching/CONTACT_2_REHEARSAL_GUIDE.md) cover their practical flows. [Recorded evidence](workbench/evidence/README.md) distinguishes fixture checks, past live runs and remaining validation gaps. New browser artifacts and evaluation reports are generated under ignored `workbench/.runtime/` folders.

## Teaching plan

| Contact | Core live work                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------- |
| 1       | Embeddings/vector RAG, Responses, structured evidence, tools, safety, traces/evaluation; basic Codex |
| 2       | PDF RAG walkthrough; governed Codex plan/build/test/review; skills, MCP, context and caching         |
| 3       | Governed publication and prepared durable/scheduled approval workflows                               |
| 4       | FDE pilot/operational decisions, incidents, handover, API/Codex readiness                            |

The [documentation index](docs/README.md) links the product design, facilitator runbook, test plan and expanded coverage blueprint. Prepared API infrastructure saves live time. Optional practice/reference material supplies breadth beyond the four-hour demonstrations.

## Honest boundaries

The default app is a **loopback-only workshop**, with synthetic data, demo identity switching, SQLite, fixture tools and a local ledger. It is not production authentication, a payment integration, a real logistics service or proof of live model quality. An explicit public hosted-workshop mode adds an HTTPS origin, secure cookies and shared request limits. Production startup remains rejected until real identity and operational controls are supplied. Advanced/reference SDK installation does not activate a service or authorize external writes.

This public repository starts with a clean Relay snapshot. Earlier game commits and tags remain in the original local repository and are not published here. Historical tag names in older evidence refer to that local history; use the documented launch profiles for this snapshot. Credentials, runtime databases, vector indexes, dependencies and raw provider reports stay local. Included screenshots use fictional workshop data; the curated evidence index distinguishes historical records from fresh local output.
