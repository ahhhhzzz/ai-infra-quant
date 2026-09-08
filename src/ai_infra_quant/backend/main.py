from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from ai_infra_quant import __version__
from ai_infra_quant.application.bootstrap import ensure_database_ready
from ai_infra_quant.backend.api.errors import problem_response, validation_exception_handler
from ai_infra_quant.backend.api.router import api_router
from ai_infra_quant.backend.dependencies import build_container
from ai_infra_quant.backend.runtime_identity import capture_source_revision
from ai_infra_quant.config import Settings
from ai_infra_quant.database.seed import bootstrap_phase_one
from ai_infra_quant.database.session import (
    create_database_engine,
    create_session_factory,
    current_migration_revision,
)
from ai_infra_quant.integrations.descriptors import (
    build_phase_one_registries,
    build_phase_one_strategy_registry,
)
from ai_infra_quant.logging_config import configure_logging

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATES = Jinja2Templates(directory=_PACKAGE_ROOT / "frontend" / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    *,
    legacy_analysis_enabled: bool = False,
) -> FastAPI:
    configure_logging()
    app_settings = settings or Settings()
    source_revision = capture_source_revision()
    database_engine = engine or create_database_engine(app_settings.database_url)
    session_factory = create_session_factory(database_engine)
    registries = build_phase_one_registries()
    strategy_registry = build_phase_one_strategy_registry()
    container = build_container(
        app_settings, database_engine, session_factory, registries, strategy_registry
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.ready = False
        revision = ensure_database_ready(current_migration_revision(database_engine))
        result = bootstrap_phase_one(session_factory, app_settings)
        del result
        application.state.migration_revision = revision
        application.state.ready = True
        yield
        database_engine.dispose()

    application = FastAPI(
        title="AI Infra Quant",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    application.state.container = container
    # Explicit in-process compatibility switch for legacy regression fixtures only.
    application.state.legacy_analysis_enabled = legacy_analysis_enabled
    application.state.ready = False
    application.state.migration_revision = None

    async def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, RequestValidationError):
            raise exc
        return await validation_exception_handler(request, exc)

    application.add_exception_handler(RequestValidationError, request_validation_handler)

    @application.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/health", response_model=None)
    def health(request: Request) -> dict[str, object] | JSONResponse:
        if not request.app.state.ready:
            return problem_response(
                request,
                status=503,
                code="DATABASE_NOT_READY",
                title="Database not ready",
                detail="The local database is not at the required application migration revision.",
            )
        return {
            "status": "OK",
            "app_version": __version__,
            "source_revision": source_revision,
            "database": "READY",
            "migration_revision": request.app.state.migration_revision,
            "trading_mode": app_settings.trading_mode.value,
            "auto_execution": app_settings.auto_execution,
        }

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard(request: Request) -> HTMLResponse:
        return _TEMPLATES.TemplateResponse(request=request, name="index.html", context={})

    application.include_router(api_router)
    application.mount(
        "/static",
        StaticFiles(directory=_PACKAGE_ROOT / "frontend" / "static"),
        name="static",
    )
    return application


app = create_app()
