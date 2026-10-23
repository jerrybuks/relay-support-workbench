---
name: browser-smoke-check
description: Verify a specified web application journey using a browser and report reproducible evidence when an engineer asks for a browser smoke check.
---

Read the requested URL, journey and expected behavior. Confirm which environment is being tested. Use a fresh disposable browser context and keep credentials out of logs and screenshots.

Exercise the stated journey with meaningful assertions: visible result, navigation, error behavior and relevant access boundary. Inspect console errors and mobile overflow when pertinent. Use the project's existing browser tooling; avoid introducing another browser stack.

Report the URL, fixture/replay/live mode, steps, assertions, result and evidence paths. Do not label intercepted or saved model responses as live. A screenshot alone is not proof that the journey passed.

Do not execute billable AI requests or externally mutating actions unless authorized. For Relay's local Contact 2 rehearsal, use the PDF journey at `/teaching/contact-2`. Inspect the provided task and use the existing Playwright setup or available browser tools. The older `contact2_browser.mjs` helper follows the Markdown exercise; it is not the PDF/page-reference browser check. The `PDF RAG` Playwright test uses intercepted provider responses and must be reported as a fixture check, not a live provider run.
