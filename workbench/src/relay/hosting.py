"""Explicit public workshop hosting with shared AI request limits; no production identity claim."""

import os
import threading
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

from fastapi.responses import JSONResponse

LOOPBACK = {"127.0.0.1", "localhost", "::1"}


class Hosting:
    def __init__(self):
        mode = os.getenv("RELAY_ENV", "local")
        if mode not in {"local", "workshop"}:
            raise RuntimeError(
                "Relay's demo identity provider is local-only by default. "
                "Use explicit workshop mode for synthetic classes; "
                "production login is not configured."
            )
        self.workshop = mode == "workshop"
        self.mode = "hosted-workshop" if self.workshop else "local-demo"
        self.origin = ""
        self.host = ""
        self.limit = 100
        self.minute_limit = 10
        self._minute = -1
        self._minute_used = 0
        self._day = ""
        self._used = 0
        self._lock = threading.Lock()
        if self.workshop:
            self.origin = os.getenv("RELAY_PUBLIC_ORIGIN", os.getenv("RENDER_EXTERNAL_URL", ""))
            url = urlsplit(self.origin)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.hostname in LOOPBACK
                or url.username
                or url.password
                or url.path not in {"", "/"}
                or url.query
                or url.fragment
            ):
                raise RuntimeError("Workshop hosting requires an exact HTTPS public origin.")
            self.origin = self.origin.rstrip("/")
            self.host = url.hostname
            self.limit = int(os.getenv("RELAY_WORKSHOP_DAILY_RUN_LIMIT", "100"))
            if not 1 <= self.limit <= 1000:
                raise RuntimeError("Workshop run limit must be between 1 and 1000.")
            self.minute_limit = int(os.getenv("RELAY_WORKSHOP_MINUTE_RUN_LIMIT", "10"))
            if not 1 <= self.minute_limit <= 100:
                raise RuntimeError("Workshop minute limit must be between 1 and 100.")

    def reject(self, request):
        host = request.url.hostname
        health = request.url.path == "/api/health" and request.method in {"GET", "HEAD"}
        if not self.workshop:
            if host not in LOOPBACK:
                return JSONResponse(
                    {"error": {"code": "local_only", "message": "Use a loopback host."}}, 403
                )
            return None
        if host != self.host and not (health and host in LOOPBACK):
            return JSONResponse({"error": {"code": "host_denied"}}, 403)
        return None

    def reserve_ai_request(self, request):
        if not self.workshop or request.method != "POST":
            return True
        path = request.url.path
        if not (
            path == "/api/v1/rag/search"
            or path.endswith("/investigations")
            or path.endswith("/investigations/stream")
            or path.endswith("/runs/stream")
        ):
            return True
        with self._lock:
            today = datetime.now(UTC).date().isoformat()
            if self._day != today:
                self._day, self._used = today, 0
            minute = int(time.time() // 60)
            if minute != self._minute:
                self._minute, self._minute_used = minute, 0
            if self._used >= self.limit or self._minute_used >= self.minute_limit:
                return False
            self._used += 1
            self._minute_used += 1
            return True
