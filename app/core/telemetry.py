import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("researchhub.http")
TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        incoming_trace_id = request.headers.get("x-trace-id", "")
        trace_id = (
            incoming_trace_id
            if TRACE_ID_PATTERN.fullmatch(incoming_trace_id)
            else str(uuid4())
        )
        request.state.trace_id = trace_id
        started_at = perf_counter()
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        logger.info(
            "http_request",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "client_ip": request.client.host if request.client else None,
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, hsts_enabled: bool = False) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.hsts_enabled = hsts_enabled

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["content-security-policy"] = (
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
            "object-src 'none'; img-src 'self' data:; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["cache-control"] = "no-store"
        if self.hsts_enabled:
            response.headers["strict-transport-security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
