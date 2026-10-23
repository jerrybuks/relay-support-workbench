# Active Relay checkpoints

The initial public Relay snapshot omits the superseded game history. Older tags named in these notes and historical reports exist only in the original local repository; the launch profiles below work directly from this snapshot.

Published Contact 2 checkpoints:

- `contact-2-before`: original working PDF app before the page-reference coding exercise; its explicit page-reference acceptance tests fail as intended.
- `contact-2-complete`: completed class implementation, updated slides and repository skills, including the staged-upload compatibility fix.

The ordinary baseline stays independent in both. Use a separate checkout and its own runtime data when switching between these checkpoints. The command's `--state before` selects the older Markdown exercise; it does not undo the page-reference feature on `main`.

Relay is the active product. The registry is [workbench/checkpoints.json](../workbench/checkpoints.json); it records explicit baseline/reference entrypoints, isolated databases and actual verification boundaries. See [reference commands](../workbench/teaching/README.md).

The source revision contains isolated teaching modules alongside baseline source. A tag alone does not choose a profile: use the registry entrypoint. Baseline startup does not import teaching modules. The Contact 2 before parser is intentionally incomplete inside its opt-in teaching app, where the optional Markdown preview reports a controlled 501. The main PDF upload/extract/chunk/index/answer demonstration works in both states. The normal application stays correct. The older duplicate-event fixture is optional practice. See the [two-hour rehearsal guide](teaching/CONTACT_2_REHEARSAL_GUIDE.md).

Use independent worktrees/browser contexts and known disposable databases. Never automatically reset Git, delete the owner's runtime database or move old tags. A fresh browser context creates a new local workspace; switching persona in the same browser preserves its workspace and rotates the session.

The initial Relay checkpoint is `relay/m0-starter`; the reference pack is `relay/teaching-reference-pack` after local verification. Both can refer to the same source revision because execution profiles are explicitly selected from isolated modules. They are not claims of separate completed live-provider branches. Content hashes in `workbench/checkpoint-files.json` make module changes reviewable.

The historical `relay/contact-1-prepared` snapshot adds the integrated opt-in live reference and updated UI. Its [preparation guide](teaching/CONTACT_1_PREPARATION.md) describes before/intermediate/live profiles with separate databases and cookies. SDK transport tests establish local integration contracts; configured live model/collector evidence remains pending.

The current working tree extends that historical snapshot with an explicitly indexed OpenAI-embedding/Qdrant RAG reference. Its local SDK/Qdrant tests are separate from live provider quality. Older tags have not been moved; use the current source/fingerprint manifest for this correction.

Legacy tags `m0-starter`, `demo/contact-1-before`, `m0-1960-starter` and `demo/1960/contact-1-before` remain untouched. Their source, evidence and original specifications are recoverable by checking out those tags in an isolated worktree. Legacy scripts and archived documents have been removed from the current working tree.

Before class, verify the intended profile, dependency lock, dataset/corpus/provider and evidence report. Real OpenAI/Langfuse/ticket/cloud integrations, customer review and timed rehearsal remain separate gates. No remote publication or real recurring task is implied by a local checkpoint.
