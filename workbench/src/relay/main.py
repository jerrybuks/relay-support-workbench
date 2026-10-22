import os
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .assistant import investigate, title_retrieval
from .hosting import Hosting
from .models import (
    Actor,
    Ask,
    CaseList,
    CaseResponse,
    Decision,
    DemoSession,
    Health,
    Investigation,
    Proposal,
    ResolutionResponse,
    SessionResponse,
)
from .service import Problem, decide, propose, require_case, require_writer
from .store import Store, encoded

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).parent / "static"


def create_app(
    db_path=None,
    retriever=title_retrieval,
    checkpoint="m0-baseline",
    store_factory=Store,
    investigator=investigate,
    provider="fixture",
    session_cookie="relay_session",
    ask_model=Ask,
    investigation_options=None,
):
    hosting = Hosting()
    store = store_factory(db_path or os.getenv("RELAY_DB", str(ROOT / ".runtime" / "relay.sqlite")))
    app = FastAPI(
        title="Relay Resolution API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        description="Local synthetic workshop. Cookie sessions; mutations require "
        "X-CSRF-Token. Credits are ledger fixtures, never real payments.",
    )
    app.state.store = store
    app.state.checkpoint = checkpoint
    app.state.session_cookie = session_cookie
    app.state.hosting = hosting

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        request.state.request_id = request_id
        rejection = hosting.reject(request)
        if rejection is not None:
            return rejection
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            expected = hosting.origin or f"{request.url.scheme}://{request.headers.get('host')}"
            if (origin and origin != expected) or request.headers.get(
                "sec-fetch-site"
            ) == "cross-site":
                return JSONResponse(
                    {"error": {"code": "origin_denied", "message": "Origin denied."}}, 403
                )
            body = await request.body()
            if len(body) > 16_384:
                return JSONResponse(
                    {"error": {"code": "body_too_large", "message": "Request too large."}}, 413
                )
        response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "Server-Timing": f"app;dur={(time.perf_counter() - started) * 1000:.2f}",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; "
                + ("style-src-attr 'unsafe-inline'; " if request.url.path == "/docs" else "")
                + "img-src 'self' data:; connect-src 'self'; "
                "frame-ancestors 'none'; base-uri 'none'; "
                "form-action 'self'",
                "Cache-Control": "no-store",
            }
        )
        return response

    @app.exception_handler(Problem)
    async def problem_handler(request, error):
        return JSONResponse(
            {
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "request_id": request.state.request_id,
                }
            },
            error.status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, error):
        # Do not echo user-supplied payloads in error objects or logs.
        return JSONResponse(
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Check the request fields.",
                    "request_id": request.state.request_id,
                }
            },
            422,
        )

    def actor(request: Request):
        identity = store.session(request.cookies.get(session_cookie))
        if not identity:
            raise Problem(401, "session_required", "Start a local demo session.")
        if request.method not in {"GET", "HEAD"}:
            if request.headers.get("x-csrf-token") != identity.csrf:
                raise Problem(403, "csrf_failed", "Refresh your session and try again.")
            if store.limited(identity):
                raise Problem(429, "rate_limited", "Too many requests. Try again in a minute.")
            if identity.role != "observer" and not hosting.reserve_ai_request(request):
                raise Problem(
                    429, "workshop_run_limit", "The workshop AI request limit is reached."
                )
        return identity

    app.state.authorize = actor

    @app.get("/api/health", tags=["Operations"], response_model=Health)
    def health():
        with store.connect() as db:
            db.execute("SELECT version FROM schema_version").fetchone()
        return {
            "status": "ok",
            "product": "relay",
            "checkpoint": checkpoint,
            "provider": provider,
            "database": "ready",
            "external_actions": False,
        }

    @app.head("/api/health", tags=["Operations"], response_class=Response)
    def health_head():
        health()
        return Response(status_code=200)

    @app.post("/api/v1/demo/session", tags=["Local identity"], response_model=SessionResponse)
    def session(data: DemoSession, request: Request):
        previous = request.cookies.get(session_cookie)
        if store.session(previous):
            actor(request)
        token, identity = store.create_session(data.role, previous)
        response = JSONResponse(
            {
                "actor": identity.model_dump(exclude={"workspace", "csrf"}),
                "csrf_token": identity.csrf,
                "mode": hosting.mode,
                "checkpoint": checkpoint,
                "provider": provider,
            }
        )
        response.set_cookie(
            session_cookie,
            token,
            httponly=True,
            samesite="strict",
            secure=hosting.workshop,
            max_age=28800,
        )
        return response

    @app.get("/api/v1/session", tags=["Local identity"], response_model=SessionResponse)
    def current(identity: Actor = Depends(actor)):
        return {
            "actor": identity.model_dump(exclude={"workspace", "csrf"}),
            "csrf_token": identity.csrf,
            "mode": hosting.mode,
            "checkpoint": checkpoint,
            "provider": provider,
        }

    @app.get("/api/v1/cases", tags=["Cases"], response_model=CaseList)
    def cases(
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        identity: Actor = Depends(actor),
    ):
        all_cases = store.cases(identity)
        return {
            "items": [
                {k: v for k, v in c.items() if k not in {"shipment", "message", "tenant"}}
                for c in all_cases[offset : offset + limit]
            ],
            "total": len(all_cases),
        }

    @app.get("/api/v1/cases/{case_id}", tags=["Cases"], response_model=CaseResponse)
    def case(case_id: str, identity: Actor = Depends(actor)):
        value = require_case(store, identity, case_id)
        return {
            "case": {k: v for k, v in value.items() if k != "tenant"},
            "messages": store.messages(identity, case_id),
            "proposals": [p for p in store.proposals(identity) if p["case_id"] == case_id],
        }

    def run_query(case_id, data, identity, **runtime_options):
        require_writer(identity)
        value = require_case(store, identity, case_id)
        before_persist = runtime_options.pop("before_persist", None)
        options = investigation_options(data) if investigation_options else {}
        result = investigator(
            store, identity, value, data.question, retriever, **(options | runtime_options)
        )
        if before_persist:
            before_persist()
        visibility = "supervisor" if identity.role == "supervisor" else "team"
        with store.transaction() as db:
            if data.remember:
                db.execute(
                    "INSERT INTO messages(workspace,case_id,question,answer,created,visibility) "
                    "VALUES (?,?,?,?,?,?)",
                    (
                        identity.workspace,
                        case_id,
                        data.question,
                        encoded(result),
                        time.time(),
                        visibility,
                    ),
                )
                # Keep only the latest 20 interactions per case; no indefinite prompt history.
                db.execute(
                    "DELETE FROM messages WHERE workspace=? AND case_id=? AND visibility=? "
                    "AND id NOT IN (SELECT id FROM messages WHERE workspace=? AND case_id=? "
                    "AND visibility=? "
                    "ORDER BY id DESC LIMIT 20)",
                    (
                        identity.workspace,
                        case_id,
                        visibility,
                        identity.workspace,
                        case_id,
                        visibility,
                    ),
                )
            store.audit(
                db,
                identity,
                "investigation.completed",
                {
                    "case_id": case_id,
                    "run_id": result["id"],
                    "provider": result["provider"],
                    "status": result["status"],
                    "source_ids": [c["id"] for c in result["citations"]],
                    "duration_ms": result["trace"]["duration_ms"],
                },
                visibility=visibility,
            )
        return result

    app.state.run_query = run_query

    @app.post(
        "/api/v1/cases/{case_id}/investigations", tags=["Assistant"], response_model=Investigation
    )
    def query(case_id: str, data: ask_model, identity: Actor = Depends(actor)):
        return run_query(case_id, data, identity)

    @app.post("/api/v1/cases/{case_id}/investigations/stream", tags=["Assistant"])
    def stream(case_id: str, data: ask_model, identity: Actor = Depends(actor)):
        # SSE transports one complete validated result; no simulated token streaming.
        result = run_query(case_id, data, identity)

        def events():
            yield f"event: completed\ndata: {encoded(result)}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.delete("/api/v1/cases/{case_id}/memory", tags=["Assistant"])
    def forget(case_id: str, identity: Actor = Depends(actor)):
        require_writer(identity)
        require_case(store, identity, case_id)
        with store.transaction() as db:
            db.execute(
                "DELETE FROM messages WHERE workspace=? AND case_id=? "
                "AND (visibility='team' OR ?='supervisor')",
                (identity.workspace, case_id, identity.role),
            )
            store.audit(db, identity, "memory.deleted", {"case_id": case_id})
        return {"status": "deleted"}

    @app.get("/api/v1/knowledge", tags=["Knowledge"])
    def knowledge(identity: Actor = Depends(actor)):
        return {
            "items": [
                {k: v for k, v in d.items() if k not in {"tenant", "tags"}}
                for d in store.documents(identity)
            ],
            "corpus": "synthetic-kora-1",
        }

    @app.post(
        "/api/v1/cases/{case_id}/proposals", tags=["Resolutions"], response_model=ResolutionResponse
    )
    def proposal(
        case_id: str,
        data: Proposal,
        idempotency_key: str = Header(default=""),
        identity: Actor = Depends(actor),
    ):
        return propose(store, identity, case_id, data, idempotency_key)

    @app.post(
        "/api/v1/proposals/{proposal_id}/decision",
        tags=["Resolutions"],
        response_model=ResolutionResponse,
    )
    def decision(
        proposal_id: str,
        data: Decision,
        idempotency_key: str = Header(default=""),
        identity: Actor = Depends(actor),
    ):
        return decide(store, identity, proposal_id, data, idempotency_key)

    @app.get("/api/v1/activity", tags=["Audit"])
    def activity(identity: Actor = Depends(actor)):
        return {"items": store.timeline(identity)}

    @app.get("/dashboard", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/", include_in_schema=False)
    @app.get("/course", include_in_schema=False)
    def course():
        return FileResponse(STATIC / "course.html")

    @app.get("/course/contact-1", include_in_schema=False)
    def contact1_presentation():
        return FileResponse(STATIC / "contact1.html")

    @app.get("/course/contact-2", include_in_schema=False)
    def contact2_presentation():
        return FileResponse(STATIC / "contact2.html")

    @app.get("/docs", include_in_schema=False)
    def api_docs():
        return FileResponse(STATIC / "swagger.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def main():
    import uvicorn

    uvicorn.run("relay.main:create_app", factory=True, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
