from __future__ import annotations

from datetime import date

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines
from src.application.services.user_plan_service import UserPlanService
from src.application.use_cases.workout.query.errors import (
    WorkoutQueryPlanNotFound,
    WorkoutQueryTodayWorkoutNotFound,
)
from src.application.use_cases.workout.query.models import TodayWorkoutViewData
from src.application.use_cases.workout.query.user_resolver import WorkoutTelegramUserResolver


class GetTodayWorkoutUseCase:
    def __init__(self, uow: UnitOfWork, user_plan_service: UserPlanService) -> None:
        self._uow = uow
        self._user_plan_service = user_plan_service
        self._user_resolver = WorkoutTelegramUserResolver(uow)

    async def get_today_workout(self, tg_user_id: int) -> TodayWorkoutViewData:
        user = await self._user_resolver.resolve_user(tg_user_id)
        plan = await self._user_plan_service.get_or_create_plan(user.id)
        if plan is None:
            raise WorkoutQueryPlanNotFound()
        today = date.today()
        async with self._uow:
            scheduled = await self._uow.scheduled_workouts.get_by_plan_and_date(plan.id, today)
        rows = ordered_lines(scheduled) if scheduled else []
        if scheduled is None or not rows:
            raise WorkoutQueryTodayWorkoutNotFound()
        return TodayWorkoutViewData(
            user_id=user.id,
            telegram_id=tg_user_id,
            scheduled=scheduled,
            rows=rows,
        )
