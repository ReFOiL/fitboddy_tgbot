from __future__ import annotations

import structlog

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.presentation.web_admin.api import create_app
from src.shared.di.bootstrap import build_container

logger = structlog.get_logger()


def create_admin_app() -> FastAPI:
    container = build_container()
    app = create_app()
    app.state.container = container

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "admin.api.error",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    logger.info("admin.app.started")
    return app

