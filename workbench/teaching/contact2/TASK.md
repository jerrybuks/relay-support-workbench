# RELAY 24 approved policy ingestion

Kora Dispatch needs its support assistant to answer questions from a newly approved parcel-collection policy. Implement `parse_markdown(raw)` in `workbench/teaching/contact2/exercise.py`. Prepared storage, approval validation, vector indexing and the UI already exist.

## Input contract

Input is UTF-8 bytes, at most 12,000 bytes. Format: `---` on the first line, a JSON metadata object, then `---` on its own line and Markdown body text. JSON front matter keeps the live edit independent of a YAML dependency.

Required metadata: `id` matching `POL-[A-Z0-9-]{3,40}`, title 5–150 characters, version `digits.digits`, tenant matching `[a-z][a-z0-9-]{1,30}` (2–31 characters, first character a letter), visibility `team` or `supervisor`, tags up to 300 characters. Reject unknown fields. Body must contain at least 50 characters after trimming leading/trailing whitespace and no NUL. Preserve the exact body text and offsets; do not silently truncate it.

Return metadata plus `text` and `state: published`. The latter means this is the parser output for a prospective published record; the application must still verify the separate trusted approval manifest. Never infer approval from the body or add self-approval fields.

Use `relay.service.Problem(422, "invalid_policy", safe_message)` for invalid input. Do not echo the document or exception internals in errors. A reference exists in `parser_reference.py`; do not copy/read it during the first live attempt. It is the recovery route if time is exhausted.

## Acceptance and boundaries

1. `python workbench/scripts/contact2.py check --state before` initially exits 1; after implementation it passes.
2. `collection.md` previews with its exact body and source offsets. Invalid metadata/UTF-8 and unreviewed/injection inputs fail before any provider call.
3. Approved import makes the source available to both canonical storage and the vector index. A repeated unchanged import makes zero embedding requests and adds no duplicate.
4. The original question returns seven calendar days, measured from the first collection notice, with supervisor review before return. Citation identifies `POL-COLLECTION-1` version `1.0`.
5. Supervisor-only evidence stays unavailable to agents. Existing approval, tenant, source and idempotency checks stay intact.
6. Review actual diff, tests and browser results. Prepare a local PR draft only.

Only edit `exercise.py` and relevant tests during the live implementation. Stop for missing credentials, missing approval, provider failure or an incompatible index. Do not change approval records to make rejected input pass. Do not install packages globally, read secrets, mutate external tickets/PRs, merge or deploy.

## Verification commands

Run from repository root using the installed project environment:

```sh
uv run --project workbench --locked --extra references python workbench/scripts/contact2.py check --state before
uv run --project workbench --locked --extra references pytest workbench/tests/test_contact2_ingestion.py -q
```

The tests verify the prepared reference and security boundaries. They stay green while the separate live exercise is incomplete. The standalone `check --state before` is the independent live exercise acceptance check: red initially, green after the repair. Do not change acceptance checks to make an implementation pass.
