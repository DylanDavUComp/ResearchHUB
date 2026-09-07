from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.telemetry import TraceIdMiddleware


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )
    app.add_middleware(TraceIdMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router)

    web_dir = Path(__file__).parent / "web"
    app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
