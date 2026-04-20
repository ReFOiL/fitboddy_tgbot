from __future__ import annotations

from src.application.services.metrics import workout_reflections_total
from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.base import WorkoutUseCaseMetrics
from src.application.use_cases.workout.callback.models import SaveReflectionRequest
from src.application.use_cases.workout.callback.resolver import WorkoutCallbackResolver


class SaveWorkoutReflectionUseCase(WorkoutUseCaseMetrics):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = WorkoutCallbackResolver(uow)

    async def save_reflection(self, request: SaveReflectionRequest) -> int:
        async def _operation() -> int:
            async with self._uow:
                user_id = await self._resolver.resolve_user_id(request.tg_user_id)
                await self._resolver.get_scheduled_for_user(user_id, request.scheduled_id)
                await self._uow.workout_reflections.upsert(
                    user_id=user_id,
                    scheduled_workout_id=request.scheduled_id,
                    energy=request.energy,
                )
                workout_reflections_total.labels(energy=str(request.energy)).inc()
                await self._uow.commit()
                return user_id

        return await self.run_with_metrics("save_workout_reflection", _operation)

