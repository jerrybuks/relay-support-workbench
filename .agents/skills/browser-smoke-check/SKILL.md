---
name: browser-smoke-check
description: Verify a specified web application journey using a browser and report reproducible evidence when an engineer asks for a browser smoke check.
---

Read the requested URL, journey and expected behavior. Confirm which environment is being tested. Use a fresh disposable browser context and keep credentials out of logs and screenshots.

Exercise the stated journey with meaningful assertions: visible result, navigation, error behavior and relevant access boundary. Inspect console errors and mobile overflow when pertinent. Use the project's existing browser tooling; avoid introducing another browser stack.

Report the URL, fixture/replay/live mode, steps, assertions, result and evidence paths. Do not label intercepted or saved model responses as live. A screenshot alone is not proof that the journey passed.

Do not execute billable AI requests or externally mutating actions unless authorized. For Relay's local Contact 2 rehearsal, use `node workbench/scripts/contact2_browser.mjs --base http://127.0.0.1:8002`; `--ask` is the explicit billable variant. This supporting command does not replace inspecting the requested journey.
