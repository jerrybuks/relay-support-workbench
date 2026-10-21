# Contact 1 preparation verification — 20 October 2026

Concepts-only presentation: a separate 15-slide deck at `/static/contact1-concepts.html` explains the existing concepts with spoken notes, diagrams and copyable code references. It contains no demo cards, profile links, code-edit directions or prescribed slide timings. The course page makes it the primary presentation link, with the original timed guide separately available. Shared navigation and styles remain consistent; reference freshness checks cover both decks. The Responses explanation explicitly distinguishes create/parse model requests, and the opening explains the support agent’s role. [Desktop](desktop-contact1-concepts.png), [mobile](mobile-contact1-concepts.png), [15-slide PDF](contact1-concepts.pdf). The new URL returned HTTP 200 through the existing live-profile static server, with no restart or provider call.

[Full verification](contact1-concepts-verify.log) passed 142 Python tests, 24 desktop/mobile checks, two opt-in Temporal skips and 95 source fingerprints. Checks cover the concepts-only contents/navigation/notes, all 15 widths and projector fit, print clipping and PDF export, original-deck compatibility, both decks’ actual code locations, and baseline packaging/isolation. This adds an explanation-only presentation; it does not claim a completed rehearsal or change the application’s teaching checkpoints.


Slide wording and code references: the participant/demo question is now “My parcel arrived late. Can I get compensation?” Slide 2 explicitly labels Qdrant as the vector database; RAG notes explain the local choice and link official references for pgvector, Pinecone, Weaviate and Milvus. Existing datasets and historical measured results retain their original questions. A zero-key check confirmed the new wording preserves the title-only miss and FTS recovery to POL-DELIVERY-3; it is not a new live-quality measurement.

Twenty-six relevant slides now carry relative `workbench/file.py:line` footnotes. Clicking copies the location for editor file search; the PDF retains the references. `contact1_references.py` resolves actual Python definitions through AST without importing teaching modules. The verification pipeline fails on stale/missing locations; the preparation guide documents regeneration. Browser checks verify actual clipboard copying, feedback and desktop/mobile/projector/PDF fit. Updated [Responses screenshot](desktop-contact1-responses.png) shows the references. [Full verification](contact1-code-references-verify.log) passed 142 Python tests, 22 browser checks, two opt-in Temporal skips and 94 source fingerprints, including reference freshness, baseline isolation and packaging. No live provider calls were made for this presentation change.


Speaker-note rewrite: all 30 notes are now conversational read-aloud talk tracks, with the opening framed around Kora Dispatch’s overloaded support team and Relay correctly identified as the application. Repeated “Additional teaching detail” dumps are removed; source links, slide bodies, timing, navigation and implementation boundaries are preserved. Demo notes explain what the presenter will open, ask, check and use as recovery. The state/stream notes reflect the actually verified OpenRouter route and its native-state limitation. [Verification](contact1-speaker-notes-verify.log) passed 142 Python tests, 22 desktop/mobile browser checks, two opt-in Temporal skips and 93 source fingerprints; the 30-slide participant PDF remains free of speaker notes. This copy change made no provider calls or readiness approval.


Course context dialog: the info button after the practical-project introduction opens only the four paragraphs of the agreed chat excerpt, beginning “Their support team is overwhelmed…” and ending with the customer’s delivery question; the longer runbook introduction is not included. A native dialog provides keyboard focus containment/restoration, close button, Escape and backdrop dismissal, with a scrolling body, fixed header and mobile sizing. It makes no provider or remote requests. [Desktop](desktop-course-context.png) and [mobile](mobile-course-context.png) captures accompany [full verification](course-context-modal-verify.log): 142 Python tests, 22 desktop/mobile browser checks, two opt-in Temporal skips and 93 source fingerprints. Browser coverage checks the agreed excerpt and four-paragraph boundary, button/keyboard opening, close/Escape dismissal, returned focus and horizontal fit.


## Harness and governance introduction — current 30-slide deck

Added two short audience slides: `#harness` uses a local, accessible SVG horse with straps/reins to distinguish model capability from the software coordinating its loop, tools, context and checks; `#governance` maps a supervisor-approval rule to backend enforcement and an accountable owner. The runtime and evaluation harness definitions are separated. Speaker notes qualify the law/police analogy: governance includes human ownership and lifecycle processes, and enforcement also lives in identity/API/database controls. They do not recommend logging hidden reasoning or every raw payload, and do not claim redaction/run caps alone guarantee privacy or exact daily spend limits. References are linked to official OpenAI harness guidance and NIST Govern.

The deck now has 15 concept slides, five demo cards and ten appendix slides. The opening case/outcomes take 30 seconds each; harness and governance take 45 seconds each; architecture takes 30 seconds. Responses still begins at minute 3, RAG at minute 4 and live demonstrations at minute 15. Navigation, contents, course copy, runbook and checkpoint counts match. Existing deep-link IDs remain stable; new IDs are `harness` and `governance`.

Desktop/mobile screenshots: [harness](desktop-contact1-harness.png), [governance](desktop-contact1-governance.png), [mobile harness](mobile-contact1-harness.png), [mobile governance](mobile-contact1-governance.png). An initial projector check caught excess height on the new slides; compact spacing fixed it. [Final full verification](contact1-harness-governance-verify.log) passed 142 Python tests and 22 desktop/mobile browser checks, with two opt-in Temporal skips, 30 printable slides without clipped content/notes, packaging/baseline isolation and 92 source fingerprints. The participant PDF is refreshed. This presentation-only work made no provider calls and does not establish a timed rehearsal or facilitator approval. Earlier deck counts below are historical.


## Successful OpenRouter live validation — 21 October 2026 / current readiness

The configured OpenRouter key now works after removing extra text before its canonical key value in the ignored env file. Live embedding preparation exposed an upstream response-model alias (`text-embedding-3-small` for requested `openai/text-embedding-3-small`). The reference now accepts only that exact same-model alias on the OpenRouter route; other-model/provider mismatches still fail. Real document embeddings built the four-chunk, 1,536-dimension Qdrant index. Credentials were never printed or committed.

**Actual live checks passed:** Responses → shipment tool → structured/cited answer; provider streaming; bounded agent loop; LangGraph workflow; manual history recall versus stateless “Unknown”; and a disposable FastAPI case journey with saved context, a streamed follow-up, preview opt-out, local history deletion and no business proposals. The actual RAG investigation trace `c4bffe3575ff4b7e872adb5aa8abc96b` was received and read back from Langfuse, beyond the earlier metadata-only connectivity probe. Initial runtime smokes used prompt 4; final evaluations, conflict and API memory/stream probe used prompt 5.

The first golden report passed 18/20. Engineering review found address questions attached to an already-delivered shipment; draft 2 binds address/damage questions to their intended synthetic cases. The next run passed 17/20 because models conflated customer eligibility with whether evidence supports the answer. Prompt 5 and schema descriptions explicitly distinguish those meanings and require empty citation IDs for abstention. **Strict validation remains unchanged.** Earlier rejected outputs/reports are retained locally, including the first conflict failure; they are useful harness examples, not overwritten successes.

Final live reports: **20/20 golden contract checks**, **8/8 unchanged held-out/adversarial candidate checks**, and the controlled conflicting-policy abstention/no-business-effect checks passed. The frozen six-case comparison completed with **6/6 checks for GPT-4o and 6/6 for GPT-4o-mini**. Listed-rate token estimates were $0.01399116 and $0.00084476 respectively; end-to-end p95 was 5,130.02 ms and 4,686.91 ms. These are single exploratory samples, not statistically established latency/quality superiority, account invoices or total preparation spend. The selected app model remains GPT-4o. Estimates use the explicitly supplied, source-linked OpenRouter card; direct-OpenAI cards remain rejected for gateway runs.

Generated answers and all original/final reports remain in ignored `workbench/.runtime/c1-preparation/openrouter-*.json`. Matching blank review templates bind facilitator labels to the final golden/held-out dataset hashes and generated evaluation fingerprints. No human labels, semantic accuracy, dataset approval or customer sign-off were invented. Safe metrics and boundaries are recorded in [current status](contact1-live-setup-status.json).

[Final local verification](contact1-openrouter-live-verify.log) passed **142 Python tests and 22 desktop/mobile browser checks**, with two opt-in Temporal skips, packaging/baseline isolation and 92 source fingerprints. **Remaining classroom gates:** facilitator review of policy labels/generated answers, a timed 60-minute rehearsal, and an explicit SDK/reference-only delivery plan for native stored chains/Conversations (unsupported on the selected gateway). The app can now be rehearsed live; full class readiness remains unapproved. Earlier account-blocked sections below are historical.


## OpenRouter route — 21 October 2026 / latest readiness

The live reference now supports explicit direct-OpenAI or OpenRouter billing routes through the same OpenAI SDK Responses/embeddings boundaries. Separate credential names, fixed endpoint pairing, namespaced gateway model IDs and a separate default vector path prevent accidental credential/index reuse. Run/session/capability/API/history/UI provider labels identify OpenRouter. The starter remains fixture-only; teaching modules remain opt-in. Gateway metadata is not native OpenAI API verification.

[Provider verification](contact1-openrouter-verify.log) passed **134 Python tests and 22 desktop/mobile browser checks**, with two opt-in Temporal skips and 91 source fingerprints. Tests exercise gateway SDK HTTP transports for embeddings/Qdrant, tool calls, structured output, streaming, caller-managed context, agent/graph execution and browser controls. These are mocked provider responses, not live answer-quality measurements. Direct-OpenAI price cards reject gateway runs. Native stored chaining and Conversations are rejected locally before gateway requests because OpenRouter documents a stateless-only Responses endpoint; the native SDK references/tests remain available.

The local env now selects OpenRouter with GPT-4o and text-embedding-3-small; direct credentials and Langfuse settings were preserved. One authorized synthetic index-build attempt reached OpenRouter and returned **HTTP 401, “Missing Authentication header”**. No successful embedding response, index manifest, generation, model evaluation or full AI-run trace is claimed. A corrected key was requested locally without exposing credentials. The earlier direct-OpenAI credit failure and actual metadata-only Langfuse receipt below remain historical evidence. See [current setup status](contact1-live-setup-status.json) and [provider configuration/commands](../../docs/teaching/CONTACT_1_PREPARATION.md#openrouter-billing-route). Class readiness remains false pending live checks, review and rehearsal.


## Account preflight and prepared experiments — 21 October 2026

The owner authorized completing demo assets and actual live preflight/evaluation after configuring local credentials. Required OpenAI/Langfuse fields and explicit opt-ins are present in ignored `workbench/.env`; no credential values were printed or committed, and the file was not changed. An authenticated model-metadata request confirmed access to the selected `gpt-4o` identifier. Embedding access is **blocked**: the initial small synthetic index attempt timed out, one bounded preparation retry returned HTTP 429, and a tiny diagnostic returned **`credit_balance_exhausted`**. Three embedding attempts produced no successful embedding/usage response. No generation request was made. A timed-out call is not assumed free. The owner was asked to replenish credit or replace the local key; “let me see” is not treated as confirmation that funding has changed. Further OpenAI calls are paused.

[Live setup status](contact1-live-setup-status.json) records this boundary. The operational vector manifest is still missing, so actual RAG/Responses/stream/state/agent/graph smokes, generated-answer evaluations, conflict semantics and measured model comparisons remain unrun. No output from local mock tests is substituted for those missing results.

Completed local assets: a draft conflicting-policy fixture and isolated actual FastAPI/Qdrant/SDK scenario (`pnpm contact1:conflict`), a frozen six-case exploratory dataset and bounded two-model comparison runner (`pnpm contact1:compare`), a dated source-linked standard-token price card, and a concrete facilitator policy-review checkpoint in the preparation guide. The scenario never modifies operational policies/cases. The comparison reserves both experiments, freezes corpus revision, retains failures and distinguishes completion from passing contract checks; no semantic approval or measured superiority is invented. Facilitator review remains required.

**Langfuse connectivity is verified live.** Authentication succeeded and a metadata-only root/child diagnostic was exported and read back: [collector receipt](contact1-langfuse-receipt.json), trace `102ea33f1da947f68585b0d9afc7a21a`. This probe made zero OpenAI calls and is not an AI investigation. Live checking exposed a retired legacy trace-read endpoint (HTTP 410), an incorrect assumption that a root must have no remote parent, and missing requested trace-context fields. The checker now uses bounded Observations API v2 reads, checks the matching trace ID and `is_root_observation`, and includes trace-context fields. The launcher sets the current ingestion-version header; full-run preflight polls receipt without repeating model calls. Source: [Langfuse migration guide](https://langfuse.com/faq/all/deprecated-api-migration).

[Final local verification](contact1-live-setup-verify.log) passed **103 Python tests and 20 desktop/mobile browser checks**, with two opt-in Temporal skips. Formatting, fixture evaluation, baseline isolation, offline packaging and **89 source fingerprints** passed. This run contains no live provider calls. Full classroom readiness and timed rehearsal remain pending.


## Participant coverage correction — 21 October 2026

The previous presentation under-taught Contact 1: Responses was reduced to a contract diagram, conversation mechanisms were obscured by generic memory language, and streaming lacked a dedicated audience slide. Passing implementation/layout tests did not establish curriculum completeness. The [participant-visible audit](../../docs/teaching/CONTACT_1_COVERAGE_AUDIT.md#participant-visible-audit--21-october-2026) now maps every Contact 1 requirement to slides, demo actions, source and evidence boundaries; earlier “complete presentation” claims are superseded here.

The corrected deck has 13 concept slides (0–15 minutes), five timed demo cards (15–60) and ten appendix slides. Audience-visible material explicitly covers OpenAI Responses SDK input/output items and structured parsing, caller-managed versus response-chain/Conversations state, typed provider streaming versus Relay SSE, cancellation and validation, plus named Langfuse and model/settings coverage. The runbook and demo notes explicitly allocate the corresponding actions. The dark visual design is preserved. Browser checks now visit these API slides with notes hidden and export the full participant PDF.

A separate `teaching/openai_state_reference.py` implements two-turn stateless/manual/previous_response_id/Conversations comparisons through the actual SDK. Five mock-HTTP tests verify outgoing context, response/conversation lineage, repeated current instructions, bounded generation attempts and cleanup attempts after failure. These tests are not evidence of live recall, real provider deletion or retention compliance. Relay's role/case/source-revalidated caller-managed memory remains unchanged; no provider-managed conversation was integrated into the case workflow.

[Fresh configuration inspection](contact1-coverage-preflight.json) explicitly loaded a local env file if present, made zero provider calls and reported no configured OpenAI key/model/live opt-in or prepared vector manifest, with `class_ready: false`. No actual model quality/usage, hosted Langfuse receipt, dataset approval or timed rehearsal is claimed. A reviewed conflicting-policy scenario and measured model/settings comparison report remain preparation gaps beyond credentials. Advanced reranking, long-term memory/compaction, parallel dispatch, moderation and managed-agent runtimes are not silently counted as implemented Contact 1 app paths.

[Final coverage verification](contact1-coverage-verify.log) passed **95 Python tests and 20 desktop/mobile checks**, with two opt-in Temporal skips. Formatting, baseline import isolation, offline packaging and **80 source fingerprints** passed. All **28 PDF slides** print without notes or clipping. Updated audience screenshots: [Responses API](desktop-contact1-responses.png), [conversation state](desktop-contact1-memory.png), [RAG](desktop-contact1-rag.png), [desktop streaming](desktop-contact1-streaming.png), [mobile streaming](mobile-contact1-streaming.png); the linked participant PDF below contains the corrected deck.


## Reference-led presentation design — 21 October 2026 / current appearance

The current deck uses the owner's [Week 2 Andela presentation](https://andela-ai-curriculum.vercel.app/week/2) as a visual reference, inspected in browser presentation mode across the cover, comparison, tool-loop and concept slides. Relay now uses a full-window dark canvas, subtle violet/blue light and dot texture, a centered title slide, compact content typography, restrained panels and quiet controls. Slide shortcuts across the bottom support direct selection and mark the current slide for assistive technology and keyboard navigation. No framework, font dependency or remote asset was added; this remains the local FastAPI-served presentation.

All 25 slide IDs and timings remain stable. Facilitator scripts, additional detail and the technical appendix are preserved; the previous peach case card and white slide surfaces are superseded. Updated screenshots and the participant PDF below show the current appearance. Focused desktop/mobile checks pass, including direct slide-shortcut selection/current-state updates, projector-height fit and PDF clipping checks. The new shortcut test caught overlapping wrapped hit areas on mobile; actual button hit areas were separated before the passing run. [Full reference-design verification](contact1-reference-design-verify.log) passed 90 Python tests and 20 desktop/mobile checks, with two opt-in Temporal tests skipped; formatting, packaging, baseline isolation and 77 source fingerprints passed. The local presentation route returned HTTP 200. Live-provider, collector and rehearsal gates remain unchanged.


## Presentation visual redesign

The audience-facing concept slides and timed demo cards now use shorter headlines, one main message and purpose-specific diagrams rather than repeated paragraph/card layouts. Navy, blue and a warm case-note accent replace the earlier presentation styling. Full facilitator scripts and additional technical explanation remain in speaker notes; the eight-slide technical appendix and all 25 stable slide links are preserved.

Focused desktop/mobile checks pass, including width checks on every slide, audience-slide navigation fitting a 1280×720 projector viewport, and a 25-page participant PDF with no clipped slides or speaker notes. An initial projector check caught the Responses slide extending below the viewport; spacing was corrected before the passing run. Updated screenshots and PDF linked below show the redesign. [Full redesign verification](contact1-redesign-verify.log) passed 90 Python tests and 20 desktop/mobile browser checks, with two opt-in Temporal tests skipped; packaging, formatting, baseline isolation and 77 source fingerprints passed. The local app was started without resetting its database and the presentation route returned HTTP 200. These are local presentation checks, with no provider-quality or rehearsal claim.


## Course page and Contact 1 presentation — current materials

The course page now reflects the expanded Contact 1 runtime, distinguishes the bounded live edit from prepared reference inspection, and links to `/course/contact-1`. The new presentation includes **12 concept slides (0–15 minutes), five demo cards (15–60 minutes) and eight appendix slides**, with speaker notes on every slide. Stable deep links, keyboard/visible navigation, contents dialog, notes view, optional elapsed rehearsal timer, fullscreen request and all-slide print/PDF are implemented without remote assets or provider calls.

[Full presentation verification](contact1-presentation-verify.log) passed **90 Python tests and 20 desktop/mobile browser checks**, with two opt-in Temporal tests skipped. Checks include concept/demo navigation, invalid fragments, speaker notes, deterministic timer pause/reset, responsive width, CSP/no external requests, and print visibility/clipping. All **25 slides** print without notes; the exported [participant PDF](contact1-presentation.pdf) contains **25 pages** (verified from its page objects). Application packaging includes the HTML/CSS/JS; **77 source fingerprints** were recorded and checked. A keyboard-navigation state-update issue found in focused QA was corrected before the final full run.

Visuals: [desktop cover](desktop-contact1-cover.png), [desktop RAG diagram](desktop-contact1-rag.png), [mobile cover](mobile-contact1-cover.png), [mobile RAG diagram](mobile-contact1-rag.png). Browser QA regenerated course screenshots. The existing local Relay process was identified, restarted without resetting its database, and `http://127.0.0.1:8000/course/contact-1` returned **HTTP 200**. The development server remains running. The Sites skill's local workflow was used; no Site was registered, published or synchronized externally.

The presentation content is complete and matches the runbook; facilitator review and an actual timed rehearsal remain open. Official OpenAI references were checked while preparing the material. No provider API call, hosted Langfuse receipt, human dataset review or completed rehearsal is claimed by these presentation checks. Earlier sections' references to an unfinished presentation are historical and superseded here.


## Coverage audit correction — current reference runtime

The [coverage audit](../../docs/teaching/CONTACT_1_COVERAGE_AUDIT.md) found further under-scoped demonstrations beyond the original embedding omission. The app reference now connects conversation context, bounded agent execution, real framework alternatives, provider streaming, nested tracing and richer evaluation to the case workflow. Earlier sections below describe historical preparation stages; their narrower boundaries are superseded by this section.

The final complete run in [runtime verification output](contact1-runtime-verify.log) passed **90 Python tests and 16 desktop/mobile browser checks**, with **two opt-in Temporal tests skipped**. Lint/format, fixture evaluation, credential-pattern scan, offline package content checks, baseline import isolation and **74 source fingerprints** passed. The initial run in that log caught a stale key after the fixture report was renamed to distinguish the lexical intermediate from the actual vector reference; that key was fixed and the final full run passed.

Actual local proof includes:

- Opt-in caller-managed context in the same investigation endpoint, default stateless behavior, role isolation, bounded recent history, stale-source rejection, unsaved/deleted context behavior and explicit model controls.
- Read-only agent iterations with exact shipment/chunk scope, whole-batch argument validation, total request/tool/turn budgets and failure closure; direct and actual LangGraph case execution. Actual LangChain chunking feeds OpenAI SDK mock embeddings and actual persistent Qdrant with exact provenance.
- Actual OpenAI SDK SSE transport parsing for successful and invalid-citation results, progress before validated completion, and early cancellation preventing another provider call or partial-answer persistence. Browser presentation fixtures independently check context/execution/runtime selections and final stage rendering.
- Actual Langfuse SDK spans with an in-memory OpenTelemetry exporter: root/run ID correlation, nested generation/tool stages, prompt/corpus metadata and payload redaction. No hosted transport is used in that test. Instrumentation records real execution timing rather than constructing stage timestamps after completion.
- Separately budgeted structured model-judge requests over actual SDK mock HTTP, inconsistent-verdict rejection, repeated/slice-capable evaluation, generated-run/dataset-bound human-label import, partial review and disagreement accounting, and cached/embedding/judge cost arithmetic from explicit synthetic test rates.
- No-network preflight inspection with a separate explicit live mode. [Actual local configuration inspection](contact1-preflight-local.json) found no configured OpenAI key/model/live opt-in and no prepared operational vector manifest, made **zero provider calls**, and reported `class_ready: false`.

The generated provider answers/embeddings/judgments in ordinary tests are mocks, not quality evidence. Actual OpenAI quality, live streaming/agent/graph behavior under the intended account, hosted Langfuse receipt and calibration remain unverified without configuration and review. No current prices, human approval, customer acceptance, real ticket/PR write, source upload, recurring job or production deployment is fabricated by these results. Older tags remain unchanged; the working-tree fingerprint manifest identifies this expanded reference.

Before Contact 1 delivery: configure and preflight the intended provider/settings, review the corpus/dataset and generated claims, confirm collector receipt if enabled, complete the presentation and rehearse. The audit separately records still-unimplemented Contact 2–3 app integrations and later practice/material work; those are not credential-only gates.


## RAG correction — current working tree

Embeddings and persistent vector retrieval were missing from the earlier prepared reference. Deferring them to advanced practice was incorrect for the agreed Contact 1 RAG demonstration. The current source corrects that gap; the historical tag remains unchanged.

The final run in [RAG verification output](rag-reference-verify.log) passed **68 Python tests and 14 desktop/mobile browser checks**, with two opt-in Temporal tests skipped, offline wheel/source packaging checks, baseline import isolation, lint/format, credential-pattern scan and **62 source fingerprints**. Earlier runs in that log caught an outdated course-text assertion; the corrected wording passed the final complete run. A final evidence-ID prompt clarification also passed the focused 26 SDK/RAG tests.

Implemented and exercised locally:

- Actual OpenAI embeddings SDK adapter, deterministic chunks with stable IDs/version hashes/exact offsets, persistent local Qdrant and authorization filtering before similarity scoring/top-k.
- Explicit index preparation with batched embedding inputs, unchanged-vector reuse and atomic manifest switching. Failed builds preserve the prior working index. Source changes and incompatible settings fail closed; removed or unauthorized sources cannot be retrieved.
- Vector retrieval by default and optional hybrid RRF comparison. Canonical chunk citations flow through the existing read-only tool/structured-answer boundary; no model business write authority was added.
- Authenticated index status and CSRF/writer-protected retrieval inspection in the live profile's Swagger; UI shows embedding usage and chunk provenance. Browser RAG presentation is a disclosed response fixture, while Python separately executes the actual SDK/Qdrant composition.
- Live evaluator uses the vector reference, records source recall/ranking and separate embedding/generation budgets and usage. A separate eight-case synthetic holdout candidate set is marked unreviewed; neither its quality nor the default cosine threshold has been calibrated.
- Optional Langfuse metadata now includes retrieval/chunk/embedding measurements; this remains a single metadata observation per completed run, not per-stage span instrumentation.

**Verification boundary:** tests run the real Qdrant engine and real OpenAI SDK over mocked HTTP embedding/Responses replies. Their hand-authored vectors demonstrate pipeline contracts and filters, not learned semantic quality. No credentials were configured, no live OpenAI embedding/generation call occurred, and no operational OpenAI-generated corpus index or hosted Langfuse delivery has been verified. The unchanged starter remains zero-key/title-only and the FTS profile remains an explicit intermediate.

Before class: configure ignored local credentials, run the explicit index command, preflight actual queries/answers, review and calibrate retrieval/answer results, confirm any enabled collector receipt and rehearse. Exact commands and data/usage boundaries are in [Contact 1 preparation](../../docs/teaching/CONTACT_1_PREPARATION.md).


Course overview follow-up: `/course` adds the participant-facing audience, outcomes, Relay workflow, four contact outlines, advanced reference/practice coverage and practice evidence. Contact 1 slides remain a subsequent deliverable. [Combined verification](course-overview-verify.log) passed **54 Python tests and 12 browser checks**, with two opt-in Temporal tests skipped and 58 source fingerprints checked. Course checks cover desktop/mobile layout, contact anchors, expandable topics and navigation to/from the workbench. The wheel includes both course assets. Screenshots: [desktop course](desktop-course.png), [mobile course](mobile-course.png). The running app was restarted and `/course` returned successfully. This work uses the Sites skill's local-only workflow; no hosted Site was registered or published.

Theme follow-up: the working tree now uses navy navigation, bright blue actions and white surfaces, with amber review highlights. [Theme verification](blue-theme-verify.log) passed 53 Python tests and 10 desktop/mobile browser checks; two opt-in Temporal tests were skipped. Screenshots below now show this palette. The existing `relay/contact-1-prepared` tag remains unchanged and preserves the earlier green theme.

Swagger follow-up: `/docs` now serves self-hosted Swagger UI 5.34.0 instead of the custom explorer. [Combined verification](swagger-verify.log) passed **54 Python tests and 10 browser checks**, with two opt-in Temporal tests skipped and 56 source fingerprints checked. Browser checks created a session directly in Swagger, read protected cases, investigated with automatic CSRF, generated/reused idempotency keys, and changed personas without stale tokens. No external requests, page errors or CSP violations were detected. Vendor hashes and packaged assets passed checks. Only `/docs` permits inline style attributes; script restrictions and workbench/API policy remain unchanged. Screenshots: [desktop Swagger](desktop-swagger.png), [mobile Swagger](mobile-swagger.png). The user-facing server was restarted and `/docs` confirmed to serve the new page.

Local starter and integrated reference contracts passed. Live OpenAI quality and hosted collector delivery remain pending: model and Langfuse credentials were not configured in this session. No live model call, source upload, external ticket write or deployment occurred.

## Reproduce

After locked dependency installation, run `pnpm verify` from the repository root. The preparation run used:

```sh
UV_CACHE_DIR=/private/tmp/relay-uv-cache uv run --project workbench --locked --extra references python workbench/scripts/verify.py --record-checkpoint
```

`--record-checkpoint` writes source fingerprints only after all preceding checks pass. Ordinary verification checks drift without updating them. See the [combined output](contact1-preparation-verify.log) and [launcher smoke results](contact1-profile-smoke.log).

| Check | Actual result |
| --- | --- |
| Python/API/reference checks | **53 passed, 2 skipped**; the two opt-in real Temporal tests were not rerun for this change |
| Desktop/mobile browser journeys | **10 passed** |
| Fixture evaluation | Starter **13/20**, retrieval reference **20/20** on the same synthetic draft set |
| Profile launch smoke | Before/retrieval HTTP servers started with disposable databases; expected paraphrase outcomes and distinct cookies confirmed; both QA servers stopped |
| Live startup guard | Missing explicit configuration fails before serving; no provider request |
| Baseline isolation | Fresh baseline import loads no teaching modules |
| Packaging | Offline source/wheel build passes; application/static files included, teaching/runtime data excluded |
| Lint/format/credential-pattern scan | Passed; pattern scan excludes environment/runtime and is not a complete security audit |
| Source fingerprints | **51 files** recorded and checked |

Browser checks cover investigate → evidence → proposal → supervisor review → persisted local credit, plus progress/run-record presentation, intentional paraphrase failure, unsaved preview/history separation and explicit failed-live-result presentation. The failed-live browser case is an intercepted presentation fixture. Python tests independently exercise the actual installed OpenAI SDK through an HTTP mock.

Integrated SDK tests cover scoped tool execution and canonical citations; timeout, refusal, incomplete output, invalid citations, unauthorized shipment and excess tool calls; no model invocation without permitted evidence; observer denial; supervisor history isolation; distinct same-host profile cookies; telemetry failure; and evaluation attempt limits with pending human review. Mock usage assertions establish plumbing, not actual billable measurements.

Screenshots: [desktop investigation](desktop-investigation.png), [desktop resolution](desktop-resolved.png), [mobile investigation](mobile-investigation.png), [mobile resolution](mobile-resolved.png).

## Issues corrected

- Unsaved responses previously entered the frontend's saved-message collection temporarily. Separate preview state now keeps saved history/counts accurate.
- Localhost ports share cookie scope. Distinct profile cookie names prevent reference sessions from replacing the starter session.
- Root `pnpm test` did not consistently discover the workbench pytest configuration. Scripts now explicitly select it.
- Source archive inspection found ignored runtime databases, a Temporal binary and earlier build output. The subdirectory build could not rely on the parent's Git ignore rules. An explicit source allowlist now produces an approximately **28 KB** archive, and verification checks the source archive as well as the wheel. The generated archive was replaced; owner's runtime databases were not deleted or modified by this correction.

Verification ran on base revision `bea2de6` with implementation changes in the working tree. The fixture report records its actual content fingerprint and dirty state; `relay/contact-1-prepared` identifies the subsequently saved snapshot. Original teaching tags remain unchanged. Baseline title matching and Contact 2–3 exercises remain isolated.

## Remaining delivery gates

Execute the configured live reference/evaluation, review generated claims and adversarial outcomes, confirm any enabled Langfuse collector delivery, review the draft dataset with a named facilitator, and rehearse the timed contact. Superseded by the RAG correction described above: FTS remains the lexical intermediate; embeddings and vector retrieval now belong to the prepared core reference. Reranking remains advanced practice. Schema/citation checks establish neither semantic accuracy nor pilot readiness. See the [Contact 1 preparation guide](../../docs/teaching/CONTACT_1_PREPARATION.md).
