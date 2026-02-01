from __future__ import annotations

from fastapi import FastAPI

from src.presentation.web_admin.api import create_app
from src.shared.di.bootstrap import build_container


def create_admin_app() -> FastAPI:
    container = build_container()
    app = create_app()
    app.state.container = container
    return app

