"""API v1: CRUD справочника мышечных групп."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import AdminPrincipal, get_current_admin
from src.presentation.web_admin.muscle_controller import MuscleController
from src.presentation.web_admin.workout_schemas import MessageOut, MuscleCreate, MuscleOut, MuscleUpdate
from src.shared.di.containers import Container

router = APIRouter()


@router.get("/muscles", response_model=list[MuscleOut])
@inject
async def list_muscles(
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: MuscleController = Depends(Provide[Container.muscle_controller]),
) -> list[MuscleOut]:
    return (await controller.list_all()).unwrap()


@router.get("/muscles/{muscle_id}", response_model=MuscleOut)
@inject
async def get_muscle(
    muscle_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: MuscleController = Depends(Provide[Container.muscle_controller]),
) -> MuscleOut:
    return (await controller.get(muscle_id)).unwrap()


@router.post("/muscles", response_model=MuscleOut)
@inject
async def create_muscle(
    data: MuscleCreate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: MuscleController = Depends(Provide[Container.muscle_controller]),
) -> MuscleOut:
    return (await controller.create(data)).unwrap()


@router.put("/muscles/{muscle_id}", response_model=MuscleOut)
@inject
async def update_muscle(
    muscle_id: int,
    data: MuscleUpdate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: MuscleController = Depends(Provide[Container.muscle_controller]),
) -> MuscleOut:
    return (await controller.update(muscle_id, data)).unwrap()


@router.delete("/muscles/{muscle_id}", response_model=MessageOut)
@inject
async def delete_muscle(
    muscle_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: MuscleController = Depends(Provide[Container.muscle_controller]),
) -> MessageOut:
    return (await controller.delete(muscle_id)).unwrap()
