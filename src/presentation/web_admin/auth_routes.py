"""Вход в админку по логину и паролю."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel, Field

from src.commons.passwords import verify_password
from src.presentation.web_admin.admin_jwt import create_admin_access_token
from src.shared.config.settings import AppSettings, get_settings
from src.shared.di.containers import Container
from src.application.interfaces.repositories import UnitOfWork

logger = structlog.get_logger()

router = APIRouter(tags=["admin-auth"])


class AdminLoginBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    is_superuser: bool


@router.post("/admin/auth/login", response_model=AdminLoginResponse)
@inject
async def admin_login(
    body: AdminLoginBody,
    uow: UnitOfWork = Depends(Provide[Container.uow]),
    settings: AppSettings = Depends(get_settings),
) -> AdminLoginResponse:
    if not settings.admin_jwt_secret.strip():
        logger.error("admin.login.jwt_secret_missing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_JWT_SECRET is not configured",
        )
    async with uow:
        account = await uow.admin_accounts.get_by_username(body.username.strip())
    if account is None or not verify_password(body.password, account.password_hash):
        logger.warning("admin.login.failed", username=body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_admin_access_token(
        settings,
        username=account.username,
        is_superuser=account.is_superuser,
    )
    expires_in = settings.admin_jwt_expire_minutes * 60
    logger.info("admin.login.ok", username=account.username)
    return AdminLoginResponse(
        access_token=token,
        expires_in=expires_in,
        is_superuser=account.is_superuser,
    )
