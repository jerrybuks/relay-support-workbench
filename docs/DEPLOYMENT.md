# Deploy the workshop frontend and backend

The frontend, FastAPI API, Swagger and slides share **one service and one HTTPS URL**. This is a public, synthetic workshop demo with selectable demo roles, not individual production accounts. AI requests are public as requested, with shared application limits.

[Deploy Relay to Render](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fjerrybuks%2Frelay-support-workbench)

## Launch on Render Free

1. Open the deployment link, sign in to Render and authorize the GitHub repository if prompted.
2. Review the Blueprint: one Docker web service on the **Free** plan, with no paid disk, database or worker. Keep the repository root as the Docker context.
3. Supply **OPENROUTER_API_KEY** in Render's secret prompt. Copy only that value from your local configuration; do not upload `.env`, credentials, local databases or vector indexes. No password or class code is required for visitors.
4. Create the service. The explicit hosted entrypoint builds embeddings for the original published synthetic policies before accepting traffic. A provider failure stops startup; it never substitutes fixture answers.
5. Open the URL Render assigns after the deploy reports **Live**. The same URL serves `/`, `/docs`, `/course` and `/course/contact-1`. Demo slide links adapt to that hosted URL.

Automatic redeploys are off so source updates do not unexpectedly reset a class workspace. After a later code change, use **Manual Deploy → Deploy latest commit** in Render.

Hosting is configured by [render.yaml](../render.yaml). Docker uses the locked Python dependencies, runs as a non-root user, binds Render's `PORT` and starts one worker. Baseline `pnpm dev` remains local and does not import hosted/reference startup code. `RELAY_ENV=production` still fails closed.

The link above lets the owner sign in and create the service in their own Render account; repository preparation and local verification do not mean a cloud service is already live.

## Free hosting and API costs

Render Free can sleep after **15 minutes without traffic**. Its filesystem is lost after a restart, redeploy or sleep: case history, approvals and the local vector index are temporary. Warm the service before class and expect the index to be rebuilt on a fresh instance. Free services cannot attach a persistent disk. See [Render's current free-plan limits](https://render.com/docs/free).

The hosting plan is free; OpenRouter model and embedding requests still consume your credits. Startup indexing uses one batched embedding request for this small synthetic corpus; a surviving compatible index reuses its existing vectors. Repeated cold starts can make new embedding requests.

Shared defaults across all browsers are **10 AI requests per minute** and **100 per UTC day**. These apply to investigations, streaming investigations and direct RAG searches; ordinary reading remains available when exhausted. The counters are in-process and reset on restart, so they are a workshop guard, not a durable billing cap. Provider output/tool/loop budgets and per-workspace limits remain in force. Use your provider account's credit controls for the spending boundary.

In Render's Environment settings, `RELAY_WORKSHOP_MINUTE_RUN_LIMIT` and `RELAY_WORKSHOP_DAILY_RUN_LIMIT` can change those application limits. Do not run multiple replicas/workers against local SQLite/Qdrant. Durable storage, real login and distributed limits require a separate deployment design.

## Verify the hosted demo

- `/api/health` returns `ok`, the live reference checkpoint and `openrouter`.
- Open RY-1042 and ask: “Can this customer receive compensation for a late express delivery?” Check its policy citation and the ₦2,000 proposal limit, subject to supervisor approval.
- Try `dlivery polcy` in Swagger's protected-by-session RAG search, or ask it in the policy assistant.
- Inspect the actual run and embedding/generation usage. Check a second browser receives a separate workspace.
- Confirm the cookie has Secure, HttpOnly and SameSite=Strict; test role, CSRF and approval boundaries before teaching online.

If the key is rejected, the account is out of credit or indexing fails, fix the Render environment and redeploy. Do not change the app to silently return fixtures. For an explicitly labelled offline host, set `RELAY_PROFILE=fixture`; this is not live RAG and requires no provider calls.

## Optional observability

Hosted trace export defaults **off**. To enable the existing metadata-only Langfuse integration, set `RELAY_TRACE_EXPORT=1` and supply `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` through Render's secret settings. Confirm an actual investigation receipt separately. These keys never belong in the Dockerfile, Blueprint or browser.

Deployment references: [Render Docker](https://render.com/docs/docker), [Blueprint specification](https://render.com/docs/blueprint-spec), [Deploy button](https://render.com/docs/deploy-to-render), and [FastAPI behind a proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/).
