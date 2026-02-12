from fastapi import FastAPI

from src.presentation.web_admin.api.v1 import api_router
from src.presentation.web_admin.webhook import router as webhook_router
from src.presentation.web_admin.questions import router as questions_router
from src.presentation.web_admin.users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="Fitboddy Admin")
    app.include_router(webhook_router, prefix="/webhooks")
    app.include_router(questions_router)
    app.include_router(users_router)
    app.include_router(api_router)
    return app

