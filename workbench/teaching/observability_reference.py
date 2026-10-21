"""Opt-in metadata-only Langfuse export. No client or background export at import."""


def safe_metadata(run):
    return {
        "run_id": run["id"],
        "provider": run["provider"],
        "status": run["status"],
        "source_ids": [c["id"] for c in run["citations"]],
        "tool_names": [t["name"] for t in run["tools"]],
        "prompt_version": run["trace"]["prompt_version"],
        "corpus_version": run["trace"]["corpus_version"],
        "duration_ms": run["trace"]["duration_ms"],
        "model": run.get("model"),
        "model_calls": run["trace"].get("model_calls", 0),
        "input_tokens": run["trace"].get("input_tokens"),
        "output_tokens": run["trace"].get("output_tokens"),
        "retrieval": run["trace"].get("retrieval"),
        "embedding_model": run["trace"].get("embedding_model"),
        "embedding_calls": run["trace"].get("embedding_calls", 0),
        "embedding_input_tokens": run["trace"].get("embedding_input_tokens"),
        "retrieval_ms": run["trace"].get("retrieval_ms"),
        "retrieved_chunks": run["trace"].get("retrieved_chunks", []),
    }


def export_metadata(client, run):
    metadata = safe_metadata(run)
    with client.start_as_current_observation(
        name="relay.investigation", as_type="span", metadata=metadata
    ) as span:
        span.update(output={"status": run["status"]})
    return metadata


# Instrument execution, rather than reconstructing stage timestamps after it finishes.
import time  # noqa: E402
from contextlib import contextmanager, nullcontext  # noqa: E402
from contextvars import ContextVar  # noqa: E402

CURRENT_RUN = ContextVar("relay_observation", default=None)


class RunObservation:
    """Local stage evidence plus optional nested Langfuse observations.

    SDK exceptions are never passed into telemetry context exits: automatic exception
    recording could export provider payloads. Only fixed stage/status metadata is sent.
    """

    def __init__(self, run_id, client=None, emit=None, session_id=None):
        self.run_id, self.client, self.emit = run_id, client, emit
        self.stages = []
        self.failed = False
        self.session_id = session_id

    @contextmanager
    def stage(self, name, kind="span", model=None):
        stage = {"name": name, "type": kind, "status": "completed"}
        started = time.perf_counter()
        manager, observation = None, None
        if self.client is not None:
            try:
                kwargs = {"name": name, "as_type": kind, "metadata": {"run_id": self.run_id}}
                if name == "relay.investigation":
                    kwargs["trace_context"] = {"trace_id": self.run_id}
                if model:
                    kwargs["model"] = model
                manager = self.client.start_as_current_observation(**kwargs)
                observation = manager.__enter__()
            except Exception:
                self.failed = True
                manager = None
        if self.emit:
            self.emit("stage", {"name": name, "status": "started"})
        try:
            yield stage
        except BaseException:
            stage["status"] = "failed"
            raise
        finally:
            stage["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            self.stages.append(stage)
            if self.emit:
                self.emit("stage", {"name": name, "status": stage["status"]})
            if observation is not None:
                try:
                    kwargs = {
                        "output": {"status": stage["status"]},
                        "metadata": {"run_id": self.run_id, "duration_ms": stage["duration_ms"]},
                    }
                    if name == "relay.investigation":
                        kwargs["metadata"].update(stage.get("metadata", {}))
                    if (
                        kind in {"generation", "embedding"}
                        and stage.get("input_tokens") is not None
                    ):
                        kwargs["usage_details"] = {
                            "input": stage["input_tokens"],
                            "output": stage.get("output_tokens", 0),
                        }
                    observation.update(**kwargs)
                except Exception:
                    self.failed = True
                finally:
                    try:
                        manager.__exit__(None, None, None)
                    except Exception:
                        self.failed = True

    @contextmanager
    def activate(self):
        token = CURRENT_RUN.set(self)
        try:
            attributes = nullcontext()
            if self.client is not None and self.session_id:
                try:
                    from langfuse import propagate_attributes

                    attributes = propagate_attributes(session_id=self.session_id)
                except Exception:
                    self.failed = True
            with self.stage("relay.investigation") as root:
                with attributes:
                    yield root
        finally:
            CURRENT_RUN.reset(token)


@contextmanager
def stage(name, kind="span", model=None):
    recorder = CURRENT_RUN.get()
    if recorder is None:
        yield {}
    else:
        with recorder.stage(name, kind, model) as measurement:
            yield measurement


def collector_received(client, trace_id):
    """Confirm an exported root through Langfuse's supported observations v2 API.

    A flush acknowledgement, an empty page or a different trace is not receipt.
    Reads are bounded by trace ID, time window and one root row; no payload fields.
    """
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    rows = client.api.observations.get_many(
        trace_id=trace_id,
        is_root_observation=True,
        from_start_time=now - timedelta(minutes=30),
        to_start_time=now + timedelta(minutes=1),
        fields="core,basic,trace_context",
        limit=1,
    )
    return any(row.trace_id == trace_id and row.is_root_observation is True for row in rows.data)
