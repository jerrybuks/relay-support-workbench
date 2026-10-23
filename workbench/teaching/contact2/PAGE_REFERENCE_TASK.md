# Contact 2 live task: PDF page references

The PDF assistant already uploads, extracts, chunks, embeds, indexes and answers. Improve its source display so an agent can find the supporting page in the original PDF.

Use `pdfs/collection-policy-multipage.pdf`: page 1 covers holding period and notice date, page 2 covers collection code and identity checks, and page 3 covers supervisor review before return.

Acceptance:

- Derive page references from extraction metadata and exact chunk offsets; do not ask the model to invent page numbers.
- Carry that information through storage and retrieval to visible passage and answer-source references.
- A passage contained on page 2 shows page 2. A passage crossing pages shows the correct range. Verify both with meaningful tests.
- Preserve canonical extracted text, existing citations, source review and tenant/role access checks. Existing ingestion and removal checks stay green.
- Show the result in the local PDF UI, inspect the diff and prepare a local PR draft with actual evidence.

Investigate and plan before editing. Use the isolated class checkout and disposable test data. The original Markdown parser task is separate practice; leave it unfinished unless explicitly assigned. Do not reset the owner's runtime data or make unauthorized provider calls or external writes.

Acceptance command (offline, disposable test data):

```sh
workbench/.venv/bin/python -m pytest -c workbench/pyproject.toml \
  workbench/teaching/contact2/reference_tests/page_reference_acceptance.py -q
```

Before state: five expected failures. Completed state: five passes. The ordinary starter regression suite stays green. Keep acceptance unchanged.

A verified facilitator reference is in `~/projects/relay-contact2-reference`, with evidence in `workbench/evidence/contact2-page-reference-preparation.json`. Do not read the recovery patch or completed implementation during the live exercise unless the instructor explicitly chooses recovery. Previously indexed PDFs need explicit removal and re-upload to capture page metadata; never reset the runtime database.
