from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.base import WorkoutUseCaseMetrics
from src.application.use_cases.workout.callback.errors import CallbackWorkoutAlreadyCompletedError
from src.application.use_cases.workout.callback.models import CompleteWorkoutRequest
from src.application.use_cases.workout.callback.resolver import WorkoutCallbackResolver


class CompleteWorkoutUseCase(WorkoutUseCaseMetrics):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = WorkoutCallbackResolver(uow)

    async def complete(self, request: CompleteWorkoutRequest) -> int:
        async def _operation() -> int:
            async with self._uow:
                user_id = await self._resolver.resolve_user_id(request.tg_user_id)
                workout = await self._resolver.get_scheduled_for_user(user_id, request.scheduled_id)
                if workout.is_completed:
                    raise CallbackWorkoutAlreadyCompletedError()
                await self._uow.scheduled_workouts.mark_completed(request.scheduled_id)
                await self._uow.commit()
                return user_id

        return await self.run_with_metrics("complete_workout", _operation)
