# Relay — Resolution desk

An API-first support workbench for a fictional Nigerian logistics company, and a practical project for four OpenAI API / Codex / AI engineering and FDE contacts.

Open a case, investigate shipment and policy evidence, propose a service credit, and review it as a supervisor. The M0 assistant is deterministic and clearly labeled; it needs no OpenAI key. No real messages or payments are sent.

## Run the new app

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --project workbench --locked
uv run --project workbench python -m relay.main
```

Open the workbench at **http://127.0.0.1:8000/dashboard**. Interactive API documentation: **http://127.0.0.1:8000/docs**.

Course homepage and four-contact learning path: **http://127.0.0.1:8000/** (also available at `/course`).

Contact 1 presentation, speaker notes and demo guide: **http://127.0.0.1:8000/course/contact-1**.

The browser starts an isolated local demo workspace as Tolu, a support agent. Open RY-1042, choose **Investigate case**, inspect policy evidence, then **Propose a service credit**. Use **Demo persona** to switch to Amara and review it. Reload preserves the workspace. Another browser/context starts independently.

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

Detailed reference commands/status are in [workbench guidance](workbench/README.md). The [Contact 1 preparation guide](docs/teaching/CONTACT_1_PREPARATION.md) covers the starter, retrieval and live-reference profiles. Live/account-dependent checks are distinct from fixture checks. See the [Contact 1 verification report](workbench/evidence/CONTACT_1_PREPARATION.md), [baseline verification report](workbench/evidence/VERIFICATION.md) and [repository cleanup verification](workbench/evidence/CLEANUP_2026-10-20.md) for actual results and remaining delivery gates.

## Teaching plan

| Contact | Core live work                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------- |
| 1       | Embeddings/vector RAG, Responses, structured evidence, tools, safety, traces/evaluation; basic Codex |
| 2       | Ticket → reproduce → Codex patch/test → browser checks → review/PR; bounded integrations             |
| 3       | Governed ingestion/skills, MCP and prepared durable/scheduled approval workflow                      |
| 4       | FDE pilot/operational decisions, incidents, handover, API/Codex readiness                            |

The [documentation index](docs/README.md) links the product design, facilitator runbook, test plan and expanded coverage blueprint. Prepared API infrastructure saves live time. Optional practice/reference material supplies breadth beyond the four-hour demonstrations.

## Honest boundaries

The default app is a **loopback-only workshop**, with synthetic data, demo identity switching, SQLite, fixture tools and a local ledger. It is not production authentication, a payment integration, a real logistics service or proof of live model quality. An explicit public hosted-workshop mode adds an HTTPS origin, secure cookies and shared request limits. Production startup remains rejected until real identity and operational controls are supplied. Advanced/reference SDK installation does not activate a service or authorize external writes.

This public repository starts with a clean Relay snapshot. Earlier game commits and tags remain in the original local repository and are not published here. Historical tag names in older evidence refer to that local history; use the documented launch profiles for this snapshot. Credentials, runtime databases, vector indexes, dependencies and raw provider reports stay local. Included screenshots use fictional workshop data; published verification logs have local machine paths replaced with placeholders and trailing whitespace normalized.
