from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.base import WorkoutUseCaseMetrics
from src.application.use_cases.workout.callback.models import SaveEffortRequest
from src.application.use_cases.workout.callback.resolver import WorkoutCallbackResolver
from src.application.workout.feedback.service import TrainingLoadAdaptationService


class SaveWorkoutEffortUseCase(WorkoutUseCaseMetrics):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = WorkoutCallbackResolver(uow)

    async def save_effort(self, request: SaveEffortRequest) -> int:
        async def _operation() -> int:
            async with self._uow:
                user_id = await self._resolver.resolve_user_id(request.tg_user_id)
                await self._resolver.get_scheduled_for_user(user_id, request.scheduled_id)
                await self._uow.scheduled_workouts.set_perceived_effort(
                    request.scheduled_id,
                    str(request.level),
                )
                adaptation = TrainingLoadAdaptationService(self._uow)
                await adaptation.apply_feedback(user_id, request.scheduled_id, str(request.level))
                await self._uow.commit()
                return user_id

        return await self.run_with_metrics("save_workout_effort", _operation)
