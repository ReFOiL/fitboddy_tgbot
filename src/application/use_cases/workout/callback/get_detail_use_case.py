from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.base import WorkoutUseCaseMetrics
from src.application.use_cases.workout.callback.errors import CallbackWorkoutNotFoundError
from src.application.use_cases.workout.callback.models import WorkoutDetailRequest, WorkoutDetailResult
from src.application.use_cases.workout.callback.resolver import WorkoutCallbackResolver
from src.application.services.scheduled_workout_lines import ordered_lines


class GetWorkoutDetailUseCase(WorkoutUseCaseMetrics):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = WorkoutCallbackResolver(uow)

    async def get_detail(self, request: WorkoutDetailRequest) -> WorkoutDetailResult:
        async def _operation() -> WorkoutDetailResult:
            async with self._uow:
                user_id = await self._resolver.resolve_user_id(request.tg_user_id)
                workout = await self._resolver.get_scheduled_for_user(user_id, request.scheduled_id)
                if not ordered_lines(workout):
                    raise CallbackWorkoutNotFoundError()
                return WorkoutDetailResult(user_id=user_id, scheduled_workout=workout)

        return await self.run_with_metrics("get_workout_detail", _operation)
