from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.callback.errors import (
    CallbackUserNotFoundError,
    CallbackWorkoutAccessDeniedError,
    CallbackWorkoutNotFoundError,
)
from src.domain.entities.training_plan import ScheduledWorkout


class WorkoutCallbackResolver:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def resolve_user_id(self, tg_user_id: int) -> int:
        user = await self._uow.users.get_by_telegram_id(tg_user_id)
        if user is None:
            raise CallbackUserNotFoundError()
        return user.id

    async def get_scheduled_for_user(self, user_id: int, scheduled_id: int) -> ScheduledWorkout:
        workout = await self._uow.scheduled_workouts.get_by_id(scheduled_id)
        if workout is None or workout.plan is None:
            raise CallbackWorkoutNotFoundError()
        if workout.plan.user_id != user_id:
            raise CallbackWorkoutAccessDeniedError()
        return workout
