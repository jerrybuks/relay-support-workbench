"""Reference-only SSE transport with real provider streaming and bounded buffering."""

import asyncio
import queue
import threading

from fastapi import Depends
from fastapi.responses import StreamingResponse

from relay.models import Actor
from relay.service import require_case, require_writer
from relay.store import encoded

from .agent_harness import LiveAsk


class RunCancelled(Exception):
    pass


def install_streaming(app):
    @app.post("/api/v1/cases/{case_id}/runs/stream", tags=["Assistant"])
    def stream(case_id: str, data: LiveAsk, actor: Actor = Depends(app.state.authorize)):
        require_writer(actor)
        require_case(app.state.store, actor, case_id)
        cancelled = threading.Event()
        events = queue.Queue(maxsize=64)

        def check_active():
            if cancelled.is_set():
                raise RunCancelled()

        def emit(name, payload):
            if not cancelled.is_set():
                try:
                    events.put_nowait((name, payload))
                except queue.Full:
                    pass  # Coalesce progress under backpressure; never queue unbounded drafts.

        def terminal(name, payload):
            while not cancelled.is_set():
                try:
                    events.put((name, payload), timeout=0.1)
                    return
                except queue.Full:
                    continue

        def produce():
            try:
                result = app.state.run_query(
                    case_id,
                    data,
                    actor,
                    stream=True,
                    emit=emit,
                    cancelled=cancelled.is_set,
                    before_persist=check_active,
                )
                terminal("completed", result)
            except RunCancelled:
                pass
            except Exception:
                terminal(
                    "failed",
                    {
                        "code": "stream_failed",
                        "message": "Investigation unavailable. Refresh the case before retrying.",
                    },
                )
            finally:
                terminal("closed", {})

        async def generate():
            worker = threading.Thread(target=produce, daemon=True, name="relay-read-only-stream")
            worker.start()
            try:
                yield "event: started\ndata: {}\n\n"
                while True:
                    try:
                        name, payload = await asyncio.to_thread(events.get, True, 1)
                    except queue.Empty:
                        yield ": waiting\n\n"
                        continue
                    if name == "closed":
                        break
                    yield f"event: {name}\ndata: {encoded(payload)}\n\n"
            finally:
                cancelled.set()

        return StreamingResponse(
            generate(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
        )
