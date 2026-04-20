from __future__ import annotations

import structlog

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.feedback.policy import (
    EffortNormalizationPolicy,
    TrainingLoadProgressionPolicy,
)

logger = structlog.get_logger()


class TrainingLoadAdaptationService:
    def __init__(
        self,
        uow: UnitOfWork,
        effort_normalization_policy: EffortNormalizationPolicy | None = None,
        progression_policy: TrainingLoadProgressionPolicy | None = None,
    ) -> None:
        self._uow = uow
        self._effort_normalization = effort_normalization_policy or EffortNormalizationPolicy()
        self._progression_policy = progression_policy or TrainingLoadProgressionPolicy()

    async def apply_feedback(
        self,
        user_id: int,
        scheduled_workout_id: int,
        effort: str,
    ) -> None:
        difficulty = self._effort_normalization.normalize(effort)
        await self._uow.workout_feedback.upsert(user_id, scheduled_workout_id, difficulty)
        await self._uow.flush()

        recent = await self._uow.workout_feedback.list_last_difficulties(user_id, limit=3)
        user = await self._uow.users.get_by_id(user_id)
        if user is None:
            return
        before = float(user.training_load_multiplier or 1.0)
        after = self._progression_policy.next_multiplier(before, recent)
        if after != before:
            user.training_load_multiplier = after
            logger.info(
                "training_load.multiplier_adjusted",
                user_id=user_id,
                before=before,
                after=after,
                last_feedback=recent,
            )
