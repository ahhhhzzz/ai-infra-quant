"""Test-only real Uvicorn composition with a labelled synthetic market provider."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from ai_infra_quant.backend.main import create_app

from .archive_support import SyntheticArchiveProvider, install


def create_archive_test_app() -> Any:
    app = create_app()
    original = app.router.lifespan_context
    provider = SyntheticArchiveProvider()

    @asynccontextmanager
    async def lifespan(application: Any) -> AsyncIterator[None]:
        async with original(application):
            install(application.state.container, provider)
            yield

    app.router.lifespan_context = lifespan

    @app.post("/_fixture/configure")
    def configure(body: dict[str, Any]) -> dict[str, Any]:
        provider.fail = set(body.get("fail", []))
        provider.delay = body.get("delay", 0)
        provider.calls.clear()
        service = install(app.state.container, provider)
        if body.get("offline"):

            def forbidden() -> Any:
                raise AssertionError("offline fixture: provider construction forbidden")

            service.provider_factory = forbidden
        return {"synthetic": True}

    @app.get("/_fixture/calls")
    def calls() -> dict[str, Any]:
        return {"calls": provider.calls}

    return app
