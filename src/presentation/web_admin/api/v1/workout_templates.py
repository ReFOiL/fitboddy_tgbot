"""API v1: CRUD шаблонов тренировок."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import get_current_admin
from src.presentation.web_admin.workout_schemas import (
    MessageOut,
    WorkoutTemplateCreate,
    WorkoutTemplateOut,
    WorkoutTemplateUpdate,
)
from src.presentation.web_admin.workout_template_controller import WorkoutTemplateController
from src.shared.di.containers import Container

router = APIRouter()


@router.get("/workout-templates", response_model=list[WorkoutTemplateOut])
@inject
async def list_workout_templates(
    _admin: str = Depends(get_current_admin),
    controller: WorkoutTemplateController = Depends(Provide[Container.workout_template_controller]),
) -> list[WorkoutTemplateOut]:
    return (await controller.list_all()).unwrap()


@router.get("/workout-templates/{template_id}", response_model=WorkoutTemplateOut)
@inject
async def get_workout_template(
    template_id: int,
    _admin: str = Depends(get_current_admin),
    controller: WorkoutTemplateController = Depends(Provide[Container.workout_template_controller]),
) -> WorkoutTemplateOut:
    return (await controller.get(template_id)).unwrap()


@router.post("/workout-templates", response_model=WorkoutTemplateOut)
@inject
async def create_workout_template(
    data: WorkoutTemplateCreate,
    _admin: str = Depends(get_current_admin),
    controller: WorkoutTemplateController = Depends(Provide[Container.workout_template_controller]),
) -> WorkoutTemplateOut:
    return (await controller.create(data)).unwrap()


@router.put("/workout-templates/{template_id}", response_model=WorkoutTemplateOut)
@inject
async def update_workout_template(
    template_id: int,
    data: WorkoutTemplateUpdate,
    _admin: str = Depends(get_current_admin),
    controller: WorkoutTemplateController = Depends(Provide[Container.workout_template_controller]),
) -> WorkoutTemplateOut:
    return (await controller.update(template_id, data)).unwrap()


@router.delete("/workout-templates/{template_id}", response_model=MessageOut)
@inject
async def delete_workout_template(
    template_id: int,
    _admin: str = Depends(get_current_admin),
    controller: WorkoutTemplateController = Depends(Provide[Container.workout_template_controller]),
) -> MessageOut:
    return (await controller.delete(template_id)).unwrap()
