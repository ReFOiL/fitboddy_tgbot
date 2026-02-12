"""API v1: CRUD упражнений."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.auth import get_current_admin
from src.presentation.web_admin.exercise_controller import ExerciseController
from src.presentation.web_admin.workout_schemas import (
    ExerciseCreate,
    ExerciseOut,
    ExerciseUpdate,
    MessageOut,
)
from src.shared.di.containers import Container

router = APIRouter()


@router.get("/exercises", response_model=list[ExerciseOut])
@inject
async def list_exercises(
    _admin: str = Depends(get_current_admin),
    controller: ExerciseController = Depends(Provide[Container.exercise_controller]),
) -> list[ExerciseOut]:
    return (await controller.list_all()).unwrap()


@router.get("/exercises/{exercise_id}", response_model=ExerciseOut)
@inject
async def get_exercise(
    exercise_id: int,
    _admin: str = Depends(get_current_admin),
    controller: ExerciseController = Depends(Provide[Container.exercise_controller]),
) -> ExerciseOut:
    return (await controller.get(exercise_id)).unwrap()


@router.post("/exercises", response_model=ExerciseOut)
@inject
async def create_exercise(
    data: ExerciseCreate,
    _admin: str = Depends(get_current_admin),
    controller: ExerciseController = Depends(Provide[Container.exercise_controller]),
) -> ExerciseOut:
    return (await controller.create(data)).unwrap()


@router.put("/exercises/{exercise_id}", response_model=ExerciseOut)
@inject
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    _admin: str = Depends(get_current_admin),
    controller: ExerciseController = Depends(Provide[Container.exercise_controller]),
) -> ExerciseOut:
    return (await controller.update(exercise_id, data)).unwrap()


@router.delete("/exercises/{exercise_id}", response_model=MessageOut)
@inject
async def delete_exercise(
    exercise_id: int,
    _admin: str = Depends(get_current_admin),
    controller: ExerciseController = Depends(Provide[Container.exercise_controller]),
) -> MessageOut:
    return (await controller.delete(exercise_id)).unwrap()
