from contextlib import contextmanager

from relay.assistant import investigate
from teaching.observability_reference import export_metadata


def test_trace_export_excludes_prompt_and_source_payload(logged, app):
    actor = app.state.store.session(logged.cookies.get("relay_session"))
    run = investigate(
        app.state.store,
        actor,
        app.state.store.case(actor, "RY-1042"),
        "private-user-input delivery credit policy",
    )
    exported = []

    class Client:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            exported.append(kwargs)
            yield self

        def update(self, **kwargs):
            exported.append(kwargs)

    metadata = export_metadata(Client(), run)
    assert metadata["provider"] == "fixture"
    assert "private-user-input" not in str(exported)
    assert "delivery fee" not in str(exported)
    assert "POL-DELIVERY-3" in metadata["source_ids"]
