# INGEST-01 — reviewed policy ingestion

Contact 3 exercise: improve one bounded path in Relay's candidate ingestion/review workflow. Read `workbench/teaching/ingestion_reference.py`, its reference tests, the separate AGENTS exercise and `workbench/teaching/skills/relay-review-policy/SKILL.md`.

Use original synthetic/local HTML inputs from the tests or add a scoped fixture beside them. Preserve provenance/rights, stable source IDs and content hashes. Reject missing fields and duplicates, strip executable HTML and treat embedded instructions as data. A queued candidate must not appear in retrieval before authenticated supervisor publication.

Acceptance: reproduce the selected gap, make the smallest justified change, verify hostile/missing-provenance/duplicate and publication-permission cases, inspect the diff and prepare a reviewed PR draft. Do not crawl unrelated sites, upload sources, invent reviewer approval or publish externally.
