from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from src.presentation.web_admin.admin_accounts_routes import router as admin_accounts_router
from src.presentation.web_admin.api.v1 import api_router
from src.presentation.web_admin.auth_routes import router as auth_router
from src.presentation.web_admin.questions import router as questions_router
from src.presentation.web_admin.users import router as users_router
from src.presentation.web_admin.user_training_plans import router as user_training_plans_router
from src.presentation.web_admin.workout_analytics import router as workout_analytics_router
from src.presentation.web_admin.webhook import router as webhook_router


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
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
    app.include_router(user_training_plans_router)
    app.include_router(workout_analytics_router)
    app.include_router(api_router)
    return app
