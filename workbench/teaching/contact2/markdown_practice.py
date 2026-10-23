"""Packaged Markdown preview for the separate parser practice, not the PDF walkthrough."""

import hashlib
import json
from pathlib import Path

from relay.service import Problem

from .config import RagConfig
from .indexing.chunking import chunks

ROOT = Path(__file__).parent


def preview(name, parser, *, tenant="kora", config=None):
    # Filename allowlist prevents traversal, symlink and arbitrary-file access.
    available = {p.name: p for p in (ROOT / "policies").glob("*.md") if not p.is_symlink()}
    if name not in available:
        raise Problem(404, "policy_not_found", "Select a packaged teaching policy.")
    raw = available[name].read_bytes()
    source = parser(raw)
    approvals = json.loads((ROOT / "approvals.json").read_text())
    review = approvals.get(name, {})
    if source["tenant"] != tenant:
        raise Problem(403, "source_tenant_denied", "Source is outside this tenant.")
    if not (
        review.get("status") == "approved"
        and review.get("sha256") == hashlib.sha256(raw).hexdigest()
        and review.get("source_id") == source["id"]
        and review.get("tenant") == source["tenant"]
        and review.get("version") == source["version"]
        and review.get("visibility") == source["visibility"]
    ):
        raise Problem(403, "source_not_approved", "A separate matching review record is required.")
    source.update(reviewed_by=review["reviewed_by"], rights=review["rights"])

    return source, chunks(source, config or RagConfig())
