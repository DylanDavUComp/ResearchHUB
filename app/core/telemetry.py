import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

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


# Unicos reproductores que un comunicado puede incrustar (modo sin cookies).
VIDEO_FRAME_SOURCES = "https://www.youtube-nocookie.com https://player.vimeo.com"

CSRF_HEADER = "X-Requested-With"
CSRF_HEADER_VALUE = "ResearchHUB"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class CsrfHeaderMiddleware(BaseHTTPMiddleware):
    """Exige un encabezado propio en las escrituras de la API.

    Otro sitio no puede enviarlo sin una autorizacion CORS explicita; junto con la
    cookie SameSite=Strict evita que se usen sesiones ajenas desde otro origen.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        if (
            request.method in UNSAFE_METHODS
            and request.url.path.startswith("/api/")
            and request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE
        ):
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "security.csrf_header_required",
                        "message": "La solicitud no proviene de la aplicación.",
                        "details": {},
                        "trace_id": getattr(request.state, "trace_id", ""),
                    }
                },
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(  # type: ignore[no-untyped-def]
        self, app, hsts_enabled: bool = False, image_origins: list[str] | None = None
    ) -> None:
        super().__init__(app)
        self.hsts_enabled = hsts_enabled
        self.img_src = " ".join(["'self'", "data:", *(image_origins or [])])

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if request.url.path.startswith("/media/"):
            # Archivos subidos: nunca se ejecutan como pagina, aunque se abran solos.
            response.headers["content-security-policy"] = (
                "default-src 'none'; frame-ancestors 'none'; sandbox"
            )
        else:
            response.headers["content-security-policy"] = (
                "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
                f"object-src 'none'; img-src {self.img_src}; script-src 'self'; "
                f"frame-src {VIDEO_FRAME_SOURCES}; "
                "style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self'"
            )
        if request.url.path.startswith("/api/"):
            response.headers["cache-control"] = "no-store"
        if self.hsts_enabled:
            response.headers["strict-transport-security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
