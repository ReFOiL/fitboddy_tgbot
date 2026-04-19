from __future__ import annotations

import structlog

from src.application.services.training_plan_admin import TrainingPlanAdminService
from src.presentation.web_admin.admin_schemas import (
    ReplaceSessionExercisesIn,
    ScheduledWorkoutOut,
    ScheduledWorkoutUpdate,
    TrainingPlanListItemOut,
    TrainingPlanOut,
    TrainingPlanUpdate,
)
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult

logger = structlog.get_logger()


class TrainingPlanAdminController(BaseController):
    def __init__(self, service: TrainingPlanAdminService) -> None:
        super().__init__()
        self._service = service

    async def get_active_plan(self, user_id: int) -> ControllerResult[TrainingPlanOut | None]:
        plan = await self._service.get_active_plan(user_id)
        if plan is None:
            return self.ok(None)
        logger.info("admin.training_plan.viewed_active", user_id=user_id, plan_id=plan.id)
        return self.ok(TrainingPlanOut.model_validate(plan))

    async def list_plans(self, user_id: int) -> ControllerResult[list[TrainingPlanListItemOut]]:
        plans = await self._service.list_plans(user_id)
        return self.ok([TrainingPlanListItemOut.model_validate(p) for p in plans])

    async def get_plan(self, user_id: int, plan_id: int) -> ControllerResult[TrainingPlanOut | None]:
        plan = await self._service.get_plan_for_user(user_id, plan_id)
        if plan is None:
            return self.not_found("План не найден")
        return self.ok(TrainingPlanOut.model_validate(plan))

    async def update_plan(
        self, user_id: int, plan_id: int, data: TrainingPlanUpdate
    ) -> ControllerResult[TrainingPlanOut | None]:
        payload = data.model_dump(exclude_unset=True, mode="python")
        try:
            plan = await self._service.update_plan(
                user_id,
                plan_id,
                start_date=payload.get("start_date"),
                end_date=payload.get("end_date"),
                status=payload.get("status"),
            )
        except ValueError as exc:
            return self.bad_request(str(exc))
        if plan is None:
            return self.not_found("План не найден")
        logger.info("admin.training_plan.updated", user_id=user_id, plan_id=plan_id)
        return self.ok(TrainingPlanOut.model_validate(plan))

    async def update_scheduled_workout(
        self, user_id: int, scheduled_id: int, data: ScheduledWorkoutUpdate
    ) -> ControllerResult[ScheduledWorkoutOut | None]:
        payload = data.model_dump(exclude_unset=True, mode="python")
        try:
            sw = await self._service.update_scheduled_workout(
                user_id,
                scheduled_id,
                scheduled_for=payload.get("scheduled_for"),
                week=payload.get("week"),
                day_of_week=payload.get("day_of_week"),
                volume_multiplier=payload.get("volume_multiplier"),
                is_completed=payload.get("is_completed"),
                completed_at=payload.get("completed_at"),
                perceived_effort=payload.get("perceived_effort"),
            )
        except ValueError as exc:
            return self.bad_request(str(exc))
        if sw is None:
            return self.not_found("Запланированная тренировка не найдена")
        logger.info(
            "admin.scheduled_workout.updated",
            user_id=user_id,
            scheduled_id=scheduled_id,
        )
        return self.ok(ScheduledWorkoutOut.model_validate(sw))

    async def replace_session_exercises(
        self, user_id: int, scheduled_id: int, data: ReplaceSessionExercisesIn
    ) -> ControllerResult[ScheduledWorkoutOut | None]:
        lines: list[tuple[int, int, int | None, int | None, int | None, int | None]] = [
            (
                row.exercise_id,
                row.sort_order,
                row.sets,
                row.reps,
                row.duration_seconds,
                row.rest_seconds,
            )
            for row in data.exercises
        ]
        try:
            sw = await self._service.replace_session_exercises(user_id, scheduled_id, lines)
        except ValueError as exc:
            return self.bad_request(str(exc))
        if sw is None:
            return self.not_found("Запланированная тренировка не найдена")
        logger.info(
            "admin.scheduled_workout.session_replaced",
            user_id=user_id,
            scheduled_id=scheduled_id,
            lines=len(lines),
        )
        return self.ok(ScheduledWorkoutOut.model_validate(sw))
