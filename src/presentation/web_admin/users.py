from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import get_current_admin
from src.presentation.web_admin.user_controller import UserController
from src.presentation.web_admin.user_schemas import UserDetailOut, UserOut
from src.shared.di import Container


router = APIRouter()


@router.get("/admin/users", response_model=list[UserOut])
@inject
async def list_users(
    _admin: str = Depends(get_current_admin),
    controller: UserController = Depends(Provide[Container.user_controller]),
) -> list[UserOut]:
    return (await controller.list_all()).unwrap()


@router.get("/admin/users/{user_id}", response_model=UserDetailOut)
@inject
async def get_user(
    user_id: int,
    _admin: str = Depends(get_current_admin),
    controller: UserController = Depends(Provide[Container.user_controller]),
) -> UserDetailOut:
    return (await controller.get_detail(user_id)).unwrap()

