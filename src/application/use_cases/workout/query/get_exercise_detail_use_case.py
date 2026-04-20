from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines
from src.application.use_cases.workout.query.errors import (
    WorkoutQueryAccessDenied,
    WorkoutQueryExerciseNotFound,
)
from src.application.use_cases.workout.query.models import ExerciseDetailViewData
from src.application.use_cases.workout.query.user_resolver import WorkoutTelegramUserResolver


class GetExerciseDetailUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._user_resolver = WorkoutTelegramUserResolver(uow)

    async def get_detail(self, tg_user_id: int, scheduled_id: int, index: int) -> ExerciseDetailViewData:
        if index < 1:
            raise WorkoutQueryExerciseNotFound()
        user = await self._user_resolver.resolve_user(tg_user_id)
        async with self._uow:
            scheduled = await self._uow.scheduled_workouts.get_by_id(scheduled_id)
            if scheduled is None or scheduled.plan is None:
                raise WorkoutQueryExerciseNotFound()
            if scheduled.plan.user_id != user.id:
                raise WorkoutQueryAccessDenied()
            rows = ordered_lines(scheduled)
            if not rows or index > len(rows):
                raise WorkoutQueryExerciseNotFound()
            workout_exercise = rows[index - 1]
            exercise = workout_exercise.exercise
            if exercise is None:
                raise WorkoutQueryExerciseNotFound()
            return ExerciseDetailViewData(
                user_id=user.id,
                telegram_id=tg_user_id,
                scheduled=scheduled,
                workout_exercise=workout_exercise,
                exercise=exercise,
            )
