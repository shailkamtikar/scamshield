"""
Protection for a public endpoint, as plain ASGI middleware so that streaming
responses pass straight through: request ids, security headers, per-IP rate
limits (free-tier API quotas must survive anonymous traffic), an optional
shared access key, and structured logs that never contain message text.
"""

import hmac
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque

from app.config import settings

log = logging.getLogger("scamshield")
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
]


class RateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.minute: dict[str, deque] = defaultdict(deque)
        self.day: dict[str, deque] = defaultdict(deque)

    def allow(self, client: str, now: float | None = None) -> tuple[bool, int]:
        now = time.time() if now is None else now
        with self.lock:
            m, d = self.minute[client], self.day[client]
            while m and now - m[0] > 60:
                m.popleft()
            while d and now - d[0] > 86400:
                d.popleft()
            if len(m) >= settings.rate_limit_per_minute:
                return False, int(60 - (now - m[0])) + 1
            if len(d) >= settings.rate_limit_per_day:
                return False, int(86400 - (now - d[0])) + 1
            m.append(now)
            d.append(now)
            if len(self.minute) > 50_000:  # never grow without bound
                self.minute.clear()
                self.day.clear()
            return True, 0


limiter = RateLimiter()


def _client_ip(scope: dict) -> str:
    headers = dict(scope.get("headers") or [])
    forwarded = headers.get(b"x-forwarded-for")
    if forwarded and settings.trust_proxy_headers:
        return forwarded.decode("latin-1").split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


class ProtectMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = uuid.uuid4().hex[:12]
        started = time.time()
        path = scope.get("path", "")
        status = {"code": 0}
        is_analysis = scope.get("method") == "POST" and path.startswith(("/investigate", "/chat"))

        async def respond(code: int, detail: str, extra: list | None = None):
            status["code"] = code
            body = json.dumps({"detail": detail, "request_id": request_id}).encode()
            await send({
                "type": "http.response.start", "status": code,
                "headers": [(b"content-type", b"application/json"), (b"x-request-id", request_id.encode()), *SECURITY_HEADERS, *(extra or [])],
            })
            await send({"type": "http.response.body", "body": body})

        async def send_wrapped(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                message.setdefault("headers", [])
                message["headers"] = [*message["headers"], (b"x-request-id", request_id.encode()), *SECURITY_HEADERS]
            await send(message)

        try:
            if is_analysis:
                if settings.api_access_key:
                    supplied = dict(scope.get("headers") or []).get(b"x-api-key", b"").decode("latin-1")
                    if not hmac.compare_digest(supplied, settings.api_access_key):
                        return await respond(401, "A valid access key is required.")
                ok, retry = limiter.allow(_client_ip(scope))
                if not ok:
                    return await respond(429, "Too many checks in a short time. Please wait a moment and try again.", [(b"retry-after", str(retry).encode())])
            try:
                await self.app(scope, receive, send_wrapped)
            except Exception:  # noqa: BLE001
                log.exception("unhandled error request_id=%s path=%s", request_id, path)
                if status["code"] == 0:
                    await respond(500, "Something went wrong on our side. Please try again.")
        finally:
            log.info(json.dumps({"id": request_id, "path": path, "status": status["code"], "ms": int((time.time() - started) * 1000)}))
