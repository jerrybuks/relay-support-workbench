"""Independent offline acceptance checks for the live parser, not model-reported completion."""

import json

from relay.service import Problem

from .markdown_practice import ROOT, preview


def check(parser):
    raw = (ROOT / "policies/collection.md").read_bytes()
    source = parser(raw)
    assert source["id"] == "POL-COLLECTION-1"
    assert source["text"] == raw.decode().split("\n---\n", 1)[1]
    assert source["state"] == "published"
    metadata = {key: value for key, value in source.items() if key not in {"text", "state"}}
    bad = [b"", b"\xff", b"x" * 12001, b"# missing header"]
    for field, value in [
        ("visibility", "public"),
        ("tenant", "../kora"),
        ("tenant", "1kora"),
        ("version", "latest"),
        ("id", "unscoped"),
        ("approved", True),
    ]:
        changed = {**metadata, field: value}
        bad.append(("---\n" + json.dumps(changed) + "\n---\n" + source["text"]).encode())
    bad.append(("---\n" + json.dumps(metadata) + "\n---\nshort").encode())
    for item in bad:
        try:
            parser(item)
        except Problem as error:
            assert error.status == 422 and error.code == "invalid_policy"
        else:
            raise AssertionError("Parser accepted an invalid source")
    for name in ["unreviewed.md", "injection.md", "missing-metadata.md", "../.env"]:
        try:
            preview(name, parser)
        except Problem as error:
            assert error.status in {403, 404, 422}
        else:
            raise AssertionError("Unapproved source accepted")
    return {"status": "passed", "checks": 1 + len(bad) + 4, "provider_calls": 0}
