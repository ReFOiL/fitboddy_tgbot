from __future__ import annotations

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from src.presentation.web_admin.admin_schemas import (
    ReplaceSessionExercisesIn,
    ScheduledWorkoutOut,
    ScheduledWorkoutUpdate,
    TrainingPlanListItemOut,
    TrainingPlanOut,
    TrainingPlanUpdate,
)
from src.presentation.web_admin.auth import AdminPrincipal, get_current_admin
from src.presentation.web_admin.training_plan_admin_controller import TrainingPlanAdminController
from src.shared.di import Container

router = APIRouter()


@router.get("/admin/users/{user_id}/training-plan", response_model=TrainingPlanOut | None)
@inject
async def get_active_training_plan(
    user_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> TrainingPlanOut | None:
    return (await controller.get_active_plan(user_id)).unwrap()


@router.get("/admin/users/{user_id}/training-plans", response_model=list[TrainingPlanListItemOut])
@inject
async def list_user_training_plans(
    user_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> list[TrainingPlanListItemOut]:
    return (await controller.list_plans(user_id)).unwrap()


@router.get("/admin/users/{user_id}/training-plans/{plan_id}", response_model=TrainingPlanOut)
@inject
async def get_user_training_plan(
    user_id: int,
    plan_id: int,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> TrainingPlanOut:
    return (await controller.get_plan(user_id, plan_id)).unwrap()


@router.put("/admin/users/{user_id}/training-plans/{plan_id}", response_model=TrainingPlanOut)
@inject
async def update_user_training_plan(
    user_id: int,
    plan_id: int,
    data: TrainingPlanUpdate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> TrainingPlanOut:
    return (await controller.update_plan(user_id, plan_id, data)).unwrap()


@router.put(
    "/admin/users/{user_id}/scheduled-workouts/{scheduled_id}",
    response_model=ScheduledWorkoutOut,
)
@inject
async def update_scheduled_workout(
    user_id: int,
    scheduled_id: int,
    data: ScheduledWorkoutUpdate,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> ScheduledWorkoutOut:
    return (await controller.update_scheduled_workout(user_id, scheduled_id, data)).unwrap()


@router.put(
    "/admin/users/{user_id}/scheduled-workouts/{scheduled_id}/session-exercises",
    response_model=ScheduledWorkoutOut,
)
@inject
async def replace_scheduled_session_exercises(
    user_id: int,
    scheduled_id: int,
    data: ReplaceSessionExercisesIn,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: TrainingPlanAdminController = Depends(
        Provide[Container.training_plan_admin_controller]
    ),
) -> ScheduledWorkoutOut:
    return (await controller.replace_session_exercises(user_id, scheduled_id, data)).unwrap()
