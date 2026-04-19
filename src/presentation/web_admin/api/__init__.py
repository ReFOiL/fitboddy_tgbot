from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from fastapi import FastAPI

from src.presentation.web_admin.admin_accounts_routes import router as admin_accounts_router
from src.presentation.web_admin.api.v1 import api_router
from src.presentation.web_admin.auth_routes import router as auth_router
from src.presentation.web_admin.questions import router as questions_router
from src.presentation.web_admin.users import router as users_router
from src.presentation.web_admin.webhook import router as webhook_router


def create_app(
    lifespan: Callable[[FastAPI], AsyncIterator[None]] | None = None,
) -> FastAPI:
    if lifespan is not None:
        app = FastAPI(title="Fitboddy Admin", lifespan=lifespan)
    else:
        app = FastAPI(title="Fitboddy Admin")
    app.include_router(webhook_router, prefix="/webhooks")
    app.include_router(auth_router)
    app.include_router(admin_accounts_router)
    app.include_router(questions_router)
    app.include_router(users_router)
    app.include_router(api_router)
    return app
