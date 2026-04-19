from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.feedback.service import TrainingLoadAdaptationService
from src.application.services.scheduled_workout_lines import ordered_lines
from src.domain.entities.training_plan import ScheduledWorkout


class WorkoutCallbackError(RuntimeError):
    pass


class CallbackUserNotFoundError(WorkoutCallbackError):
    pass


class CallbackWorkoutNotFoundError(WorkoutCallbackError):
    pass


class CallbackWorkoutAccessDeniedError(WorkoutCallbackError):
    pass


class CallbackWorkoutAlreadyCompletedError(WorkoutCallbackError):
    pass


@dataclass(slots=True)
class WorkoutDetailResult:
    user_id: int
    scheduled_workout: ScheduledWorkout


class WorkoutCallbackUseCases:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_detail(self, tg_user_id: int, scheduled_id: int) -> WorkoutDetailResult:
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(tg_user_id)
            if user is None:
                raise CallbackUserNotFoundError()
            workout = await self._scheduled_for_user(user.id, scheduled_id)
            if workout is None or not ordered_lines(workout):
                raise CallbackWorkoutNotFoundError()
            return WorkoutDetailResult(user_id=user.id, scheduled_workout=workout)

    async def complete_workout(self, tg_user_id: int, scheduled_id: int) -> int:
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(tg_user_id)
            if user is None:
                raise CallbackUserNotFoundError()
            workout = await self._scheduled_for_user(user.id, scheduled_id)
            if workout is None:
                raise CallbackWorkoutNotFoundError()
            if workout.is_completed:
                raise CallbackWorkoutAlreadyCompletedError()
            await self._uow.scheduled_workouts.mark_completed(scheduled_id)
            await self._uow.commit()
            return user.id

    async def save_effort(
        self,
        tg_user_id: int,
        scheduled_id: int,
        level: str,
    ) -> int:
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(tg_user_id)
            if user is None:
                raise CallbackUserNotFoundError()
            workout = await self._scheduled_for_user(user.id, scheduled_id)
            if workout is None:
                raise CallbackWorkoutAccessDeniedError()

            await self._uow.scheduled_workouts.set_perceived_effort(scheduled_id, level)
            adaptation = TrainingLoadAdaptationService(self._uow)
            await adaptation.record_feedback_and_adjust_multiplier(user.id, scheduled_id, level)
            await self._uow.commit()
            return user.id

    async def _scheduled_for_user(
        self,
        user_id: int,
        scheduled_id: int,
    ) -> ScheduledWorkout | None:
        workout = await self._uow.scheduled_workouts.get_by_id(scheduled_id)
        if workout is None or workout.plan is None:
            return None
        if workout.plan.user_id != user_id:
            return None
        return workout
