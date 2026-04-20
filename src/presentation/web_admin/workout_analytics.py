from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.presentation.web_admin.admin_schemas import WorkoutAnalyticsSummaryOut
from src.presentation.web_admin.auth import AdminPrincipal, get_current_admin
from src.presentation.web_admin.workout_analytics_controller import WorkoutAnalyticsController

router = APIRouter()


@router.get("/admin/analytics/workouts/summary", response_model=WorkoutAnalyticsSummaryOut)
@inject
async def get_workout_analytics_summary(
    goal: str | None = None,
    level: str | None = None,
    workout_location: str | None = None,
    equipment: str | None = None,
    _admin: AdminPrincipal = Depends(get_current_admin),
    controller: WorkoutAnalyticsController = Depends(
        Provide["workout_analytics_controller"]
    ),
) -> WorkoutAnalyticsSummaryOut:
    return (
        await controller.get_summary(
            goal=goal,
            level=level,
            workout_location=workout_location,
            equipment=equipment,
        )
    ).unwrap()

