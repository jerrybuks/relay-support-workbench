"""Verified parser reference. Document prose never supplies approval or execution authority."""

import json

from pydantic import Field, ValidationError

from relay.models import Contract
from relay.service import Problem


class PolicyMetadata(Contract):
    id: str = Field(pattern=r"^POL-[A-Z0-9-]{3,40}$")
    title: str = Field(min_length=5, max_length=150)
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    tenant: str = Field(pattern=r"^[a-z][a-z0-9-]{1,30}$")
    visibility: str = Field(pattern=r"^(team|supervisor)$")
    tags: str = Field(max_length=300)


def parse_markdown(raw):
    """JSON front matter between --- lines; preserve exact canonical body bytes as text."""
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 12_000:
        raise Problem(422, "invalid_policy", "Use a UTF-8 policy file up to 12,000 bytes.")
    try:
        text = raw.decode("utf-8")
        if not text.startswith("---\n"):
            raise ValueError
        header, body = text[4:].split("\n---\n", 1)
        metadata = PolicyMetadata.model_validate(json.loads(header))
        if len(body.strip()) < 50 or "\x00" in body:
            raise ValueError
    except (UnicodeError, ValueError, ValidationError):
        raise Problem(
            422, "invalid_policy", "Check policy metadata and readable UTF-8 body."
        ) from None
    return {**metadata.model_dump(), "text": body, "state": "published"}
