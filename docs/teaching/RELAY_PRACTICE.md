# Relay participant practice and FDE evidence

These exercises supply depth beyond the four facilitated hours. They are assignments with acceptance criteria, not claims of completed reference implementations. Use synthetic data and isolated branches. Participants can start after Contact 3; Contact 4 does not require presentations.

## Foundation outcomes

1. **Discover a useful workflow.** Interview or role-play a support agent and supervisor. Identify the costly step, data owners, constraints and a non-AI alternative. Submit a one-page problem/acceptance brief with baseline and pilot metrics. Distinguish assumptions from verified customer findings.
2. **Deliver grounded assistance.** Improve the title-only retrieval baseline, compare lexical/vector/hybrid retrieval and reranking on a held-out set, and provide exact passage citations. Measure retrieval separately from answer support. Test conflicting, stale, deleted and restricted sources. No unreviewed corpus publication.
3. **Engineer a tool loop.** Execute only allowlisted read tools, validate arguments, bound turns/tool count/time/cost, and test unknown tools, malformed arguments, repeated actions and unavailable services. Inspect the whole action sequence. Compare deterministic orchestration with agent selection.
4. **Handle state and memory.** Compare stateless, caller-managed history and supported server conversation state. Exercise context compaction and task continuity. Define retention/deletion and verify role/tenant isolation after permission changes. Do not equate transcript persistence with semantic long-term memory.
5. **Build an evaluation harness.** Review a golden set, reserve held-out cases, add deterministic checks and calibrated model judges, run repeat experiments, report failure slices and cost per successful task. Keep dataset/prompt/model/corpus versions. Synthetic fixture success is not customer validation.
6. **Make one durable workflow.** Trigger a freshness or resolution task, pause for an exact-action approval, stop/restart its worker, resume safely and retry an event. Verify one external/local effect, cancellation, rejection, timeout and conflicting payload behavior. Inspect a timezone-aware schedule, overlap/catch-up policy and pause/delete lifecycle.
7. **Use Codex to deliver a bounded issue.** Read a scoped ticket through MCP, reproduce it, propose a plan, patch in an isolated worktree, test and browser-verify, review the diff and prepare a PR. Demonstrate a stopping condition and rejected overbroad change. Use a skill and scoped AGENTS.md guidance. Real ticket/PR writes need explicit authorization.
8. **Prepare an FDE pilot handover.** Propose success thresholds, rollout cohort, operator, support ownership, incident/escalation and rollback plan. Explain identity/integration/data constraints, economics and user adoption. Rehearse an outage and show evidence for go/conditional/no-go.

## Advanced comparisons

| Topic                             | Assignment                                                                          | Evidence                                                                                      |
| --------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Model/reasoning selection         | Compare supported settings/models on fixed cases                                    | Quality, token usage, p95 latency and cost per success; no best-model claim from one response |
| Prompt caching/batch/flex         | Choose an appropriate workload and processing mode                                  | Measured cache/throughput/cost data and disclosed trade-offs                                  |
| Context engineering               | Version prompts, select/compact context and preserve constraints                    | Long-conversation regression; no secret source in unauthorized context                        |
| Multi-agent                       | Split independent work with explicit budgets and merge rules                        | Compare against one agent, including duplicated effort, latency/cost and conflicting outputs  |
| Tool discovery/programmatic calls | Use supported runtime features with a larger tool surface                           | Correct tool/arguments, bounded execution and comparison against direct calls                 |
| Multimodal RAG                    | Ingest a permitted PDF/image and preserve extraction provenance                     | Page/region references, extraction uncertainty and reviewed publication                       |
| Voice/realtime                    | Add voice intake for a synthetic support case                                       | Turn-taking, interruption/cancellation, server tool permissions and latency                   |
| Fine-tuning/distillation          | Decide whether adaptation addresses an observed failure                             | Data suitability, supported platform status, held-out comparison and deletion/retention plan  |
| Langfuse                          | Link evaluations to redacted application traces                                     | Prompt/model/corpus versions, failed tools, timings and feedback-to-regression loop           |
| Runtime choices                   | Compare direct Responses, Agents SDK, managed runtime, LangGraph and Temporal roles | One clear ownership diagram; avoid duplicated retries/authority                               |
| Scheduling and skills             | Reuse a skill in a scheduled development/business task                              | Manual run first; inspect permissions, history, overlap, pause/cancel and review boundary     |
| Codex SDK/CI/cloud                | Run an approved scoped task programmatically                                        | Actual run ID/mode, structured output, isolated workspace and human-reviewed diff             |
| Windsurf comparison               | Use the same task and acceptance criteria as Codex                                  | Observed differences without unsupported general performance claims                           |
| MCP governance                    | Inspect tool capabilities, identity/scopes and untrusted results                    | Denied out-of-scope call; secrets/egress/approval threat model                                |

## Assessment

Review correctness, reproducibility, authorization, evidence quality, operational judgment and clear customer communication. Each submission identifies what ran live, locally, as a fixture or not at all. Attendance and topic exposure alone do not establish implementation proficiency or certification readiness.

Official certification materials remain separate inputs; do not claim this project reproduces every current exam objective without mapping the actual course objectives.
