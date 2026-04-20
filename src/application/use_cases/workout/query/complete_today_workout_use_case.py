from __future__ import annotations

from datetime import date

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.application.use_cases.workout.query.errors import (
    WorkoutQueryAlreadyCompleted,
    WorkoutQueryPlanNotFound,
    WorkoutQueryTodayWorkoutNotFound,
)
from src.application.use_cases.workout.query.models import CompletedTodayWorkoutData
from src.application.use_cases.workout.query.user_resolver import WorkoutTelegramUserResolver


class CompleteTodayWorkoutUseCase:
    def __init__(self, uow: UnitOfWork, user_plan_service: UserPlanService) -> None:
        self._uow = uow
        self._user_plan_service = user_plan_service
        self._user_resolver = WorkoutTelegramUserResolver(uow)

    async def complete_today(self, tg_user_id: int) -> CompletedTodayWorkoutData:
        user = await self._user_resolver.resolve_user(tg_user_id)
        plan = await self._user_plan_service.get_or_create_plan(user.id)
        if plan is None:
            raise WorkoutQueryPlanNotFound()
        today = date.today()
        async with self._uow:
            scheduled = await self._uow.scheduled_workouts.get_by_plan_and_date(plan.id, today)
            if scheduled is None:
                raise WorkoutQueryTodayWorkoutNotFound()
            if scheduled.is_completed:
                raise WorkoutQueryAlreadyCompleted()
            await self._uow.scheduled_workouts.mark_completed(scheduled.id)
            await self._uow.commit()
        return CompletedTodayWorkoutData(
            user_id=user.id,
            telegram_id=tg_user_id,
            scheduled_workout_id=scheduled.id,
            scheduled_for_iso=scheduled.scheduled_for.isoformat(),
        )
