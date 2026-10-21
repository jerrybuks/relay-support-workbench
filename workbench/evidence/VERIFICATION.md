# Relay local verification — 19 October 2026

Latest Contact 1/UI/packaging verification: [20 October preparation report](CONTACT_1_PREPARATION.md). Results below describe the original foundation run; screenshot paths now show the updated UI.

Result: the new local baseline and isolated teaching references passed the combined verification. This is not production readiness or proof of live provider/customer integration.

## Reproduce

From the repository root, after locked dependency installation:

```sh
uv sync --project workbench --locked --extra references
uv run --project workbench --locked --extra references python workbench/scripts/verify.py --with-temporal
```

The preparation run used `UV_CACHE_DIR=/private/tmp/relay-uv-cache` because the environment restricts writes to the default cache. See [actual combined output](verify.log). Without `--with-temporal`, the two real-server tests are explicitly skipped. No OpenAI request or external ticket/payment write is made by this verification.

## Passed checks

| Check | Actual result |
| --- | --- |
| Python lint and format | Ruff passed; 38 Python files formatted |
| Repository formatting | Prettier passed |
| API/security/reference suite | **43 passed**, including both actual local Temporal integration tests |
| Desktop/mobile browser | **6 passed**; investigation → evidence → proposal → supervisor decision → reload, navigation, search, memory deletion, observer restrictions and offline API explorer |
| Fixture evaluation | Starter **13/20**; Contact 1 lexical reference **20/20**, same draft synthetic dataset |
| Credential-pattern scan | No findings across 151 source/document files at scan time; pattern scan only, runtime/environment excluded |
| Baseline import boundary | Fresh baseline process loaded no teaching modules |
| Package build | Source archive and wheel built successfully offline; wheel includes frontend assets and excludes teaching/runtime data |
| Content fingerprints | **47 files** matched `workbench/checkpoint-files.json` |
| Git whitespace check | Passed |

Browser artifacts: [desktop investigation](desktop-investigation.png), [desktop resolution](desktop-resolved.png), [mobile investigation](mobile-investigation.png), [mobile resolution](mobile-resolved.png).

The actual CLI Contact 2 reproduction was also run separately: [before](contact2-before.log) exits 1 with ₦4,000 actual/₦2,000 expected; [reference](contact2-reference.log) exits 0 with ₦2,000. Its deliberately broken function is never imported by the baseline.

The packaged `relay-review-policy` skill passed the Skill Creator frontmatter/scaffold validator. API ingestion tests additionally prove candidate isolation, script stripping, duplicate rejection and supervisor publication. Syntax validation alone does not establish agent skill quality.

## What the reference checks prove

- **Contact 1:** independently selected lexical passage/tag retrieval improves the disclosed fixture set. Actual installed OpenAI SDK parsing is exercised through an HTTP mock, alongside citation allowlists/refusal handling and bounded read-tool authority. This is not an embedding/reranking or live model quality benchmark.
- **Contact 2:** intentional red/green reproduction, conflicting replay rejection, baseline concurrent approval protection, and actual MCP SDK allowed/denied fixture-ticket calls. No Linear/GitHub/Codex-cloud account action was performed.
- **Contact 3:** reviewed candidate publication and actual LangChain chunking/LangGraph state graph; a Temporal worker stops while waiting for review, duplicate approval signals arrive without a worker, a replacement worker resumes, and one ledger effect results. A second real dev-server test registers a timezone-aware schedule, triggers a synthetic freshness run immediately, checks its result, pauses and deletes the schedule. No recurring schedule remains.
- **Observability:** metadata-only Langfuse adapter contract is tested without hosted export. It does not send prompts, raw source passages or credentials.

## Issues found and resolved

1. Generic lexical matches could produce policy evidence for a restricted-source question without leaking the restricted source. Added a minimum lexical evidence threshold to the reference. This is a fixture heuristic and still needs live semantic evaluation.
2. Supervisor answers could have reappeared through saved context after a role switch. Migration 2 restricts saved context and investigation traces by role; an agent cannot read/delete supervisor context. A regression verifies the boundary. Older context is conservatively supervisor-only during upgrade.
3. Full-page screenshots exposed an offscreen skip link/sticky offset. Corrected skip-link clipping and screenshot scroll position; browser workflow remained accessible.
4. Temporal SDK's fixed five-second dev-server startup check failed intermittently on cold launch. The schedule harness now pins CLI 1.9.1, uses the official curl download transport, waits explicitly for service readiness for up to 30 seconds and guarantees process teardown. The final combined run passed both server tests. [Earlier failure output](temporal-startup-failure.log) is retained for provenance. The SDK time-skipping server emits a heartbeat-capability warning; these tests do not exercise activity heartbeat recovery.

## Versions and source identity

Reference runtime: Python 3.12.13, uv 0.12.3. Locked versions include FastAPI 0.148.0, Pydantic 2.14.1, Uvicorn 0.54.0, pytest 9.1.1, OpenAI SDK 3.35.1, MCP SDK 2.3.0, Langfuse 4.18.0, LangGraph 1.2.16 and Temporal SDK 1.34.0. The schedule dev CLI is 1.9.1 / server 1.32.0. Exact transitive dependencies are in `workbench/uv.lock`.

Verification ran before the new checkpoint commit. The [evaluation JSON](fixture-evaluation.json) therefore records the previous base Git revision and a dirty working tree, plus its actual content fingerprint. This is intentional disclosure. `relay/m0-starter` and `relay/teaching-reference-pack` identify the subsequently saved snapshot; their isolated execution profiles are recorded in `workbench/checkpoints.json`. Both tags can identify the same source revision because reference selection is explicit, not an automatic checkout effect.

## Remaining delivery gates

- Facilitator/domain review of the synthetic corpus and draft golden set; representative held-out and adversarial live evaluations.
- Authorized live OpenAI/model/hosted retrieval measurements and Langfuse export. Fixture correctness does not establish model accuracy, semantic citation support, live latency or usage.
- Real Codex CLI/cloud, Linear/GitHub and reviewed PR workflow preflight. Local task files/protocol fixtures do not establish remote integration success.
- Advanced practice implementations and full timed contact rehearsal; map the actual official participant course objectives before claiming certification coverage.
- Customer discovery/acceptance, production identity, managed persistence/rate limits, retention/residency, monitoring, incident ownership and rollout/rollback review before any real deployment.

The user-facing loopback app remains available on port 8000. QA servers and schedules are disposable. The original checkpoints preserve the earlier game; its working-tree files were subsequently removed on 20 October 2026. See the [cleanup verification note](CLEANUP_2026-10-20.md) for the current repository checks.
