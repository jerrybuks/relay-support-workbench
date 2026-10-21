"""A controlled conflict corpus in an isolated reference app; never seed operational policies."""

import json
from pathlib import Path

from .contact1_live import create_app

FIXTURE = Path(__file__).resolve().parents[1] / "evals/conflicting-policy.json"


def scenario():
    return json.loads(FIXTURE.read_text())


def conflict_documents(documents):
    original = next((d for d in documents if d["id"] == "POL-DELIVERY-3"), None)
    if original is None:
        return documents
    # Start with the actor's canonical allowed documents; preserve ACL metadata.
    policies = [{**original, **p} for p in scenario()["policies"]]
    return [d for d in documents if d["id"] != original["id"]] + policies


def create_conflict_app(*args, **kwargs):
    app = create_app(*args, **kwargs)
    canonical = app.state.store.documents
    app.state.store.documents = lambda actor: conflict_documents(canonical(actor))
    return app
