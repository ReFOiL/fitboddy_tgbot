"""Учётные записи админки: список и создание (только суперпользователь)."""
from __future__ import annotations

from datetime import datetime

import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError

from src.application.interfaces.repositories import UnitOfWork
from src.commons.passwords import hash_password
from src.domain.entities.admin_account import AdminAccount
from src.presentation.web_admin.auth import AdminPrincipal, require_superuser
from src.shared.di.containers import Container

logger = structlog.get_logger()

router = APIRouter(tags=["admin-accounts"])


class AdminAccountOut(BaseModel):
    id: int
    username: str
    is_superuser: bool
    created_at: datetime


class AdminAccountCreateBody(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class AdminAccountUpdateBody(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def at_least_one_field(self) -> AdminAccountUpdateBody:
        if self.username is None and self.password is None:
            raise ValueError("Provide username and/or password")
        return self


def _to_out(a: AdminAccount) -> AdminAccountOut:
    return AdminAccountOut(
        id=a.id,
        username=a.username,
        is_superuser=a.is_superuser,
        created_at=a.created_at,
    )


@router.get("/admin/admin-accounts", response_model=list[AdminAccountOut])
@inject
async def list_admin_accounts(
    _: AdminPrincipal = Depends(require_superuser),
    uow: UnitOfWork = Depends(Provide[Container.uow]),
) -> list[AdminAccountOut]:
    async with uow:
        rows = await uow.admin_accounts.list_all()
    return [_to_out(a) for a in rows]


@router.post("/admin/admin-accounts", response_model=AdminAccountOut, status_code=status.HTTP_201_CREATED)
@inject
async def create_admin_account(
    body: AdminAccountCreateBody,
    principal: AdminPrincipal = Depends(require_superuser),
    uow: UnitOfWork = Depends(Provide[Container.uow]),
) -> AdminAccountOut:
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is empty")
    account = AdminAccount(
        username=username,
        password_hash=hash_password(body.password),
        is_superuser=False,
    )
    try:
        async with uow:
            await uow.admin_accounts.add(account)
            await uow.flush()
            await uow.commit()
            await uow.refresh(account)
    except IntegrityError as e:
        logger.warning("admin.account.duplicate", username=username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from e
    logger.info("admin.account.created", username=username, by=principal.username)
    return _to_out(account)


@router.patch("/admin/admin-accounts/{account_id}", response_model=AdminAccountOut)
@inject
async def update_admin_account(
    account_id: int,
    body: AdminAccountUpdateBody,
    principal: AdminPrincipal = Depends(require_superuser),
    uow: UnitOfWork = Depends(Provide[Container.uow]),
) -> AdminAccountOut:
    async with uow:
        account = await uow.admin_accounts.get_by_id(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        if body.username is not None:
            new_username = body.username.strip()
            if not new_username:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is empty")
            account.username = new_username
        if body.password is not None:
            account.password_hash = hash_password(body.password)
        try:
            await uow.flush()
            await uow.commit()
            await uow.refresh(account)
        except IntegrityError as e:
            logger.warning("admin.account.duplicate_update", account_id=account_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            ) from e
    logger.info("admin.account.updated", account_id=account_id, by=principal.username)
    return _to_out(account)


@router.delete("/admin/admin-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_admin_account(
    account_id: int,
    principal: AdminPrincipal = Depends(require_superuser),
    uow: UnitOfWork = Depends(Provide[Container.uow]),
) -> None:
    async with uow:
        actor = await uow.admin_accounts.get_by_username(principal.username)
        if actor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account not found for this token",
            )
        target = await uow.admin_accounts.get_by_id(account_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        if target.id == actor.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )
        if target.is_superuser:
            super_count = await uow.admin_accounts.count_superusers()
            if super_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last superuser",
                )
        await uow.admin_accounts.delete(account_id)
        await uow.commit()
    logger.info("admin.account.deleted", account_id=account_id, by=principal.username)
