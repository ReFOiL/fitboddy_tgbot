from __future__ import annotations

from sqlalchemy import delete, select

from src.application.interfaces.repositories import IWorkoutFeedbackRepository
from src.domain.entities.workout_feedback import WorkoutFeedback
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class WorkoutFeedbackRepository(SQLAlchemyRepository, IWorkoutFeedbackRepository):
    async def upsert(self, user_id: int, scheduled_workout_id: int, difficulty: str) -> None:
        await self._session.execute(
            delete(WorkoutFeedback).where(
                WorkoutFeedback.user_id == user_id,
                WorkoutFeedback.scheduled_workout_id == scheduled_workout_id,
            )
        )
        self._session.add(
            WorkoutFeedback(
                user_id=user_id,
                scheduled_workout_id=scheduled_workout_id,
                difficulty=difficulty,
            )
        )
        await self._session.flush()

    async def list_last_difficulties(self, user_id: int, *, limit: int = 3) -> list[str]:
        result = await self._session.execute(
            select(WorkoutFeedback.difficulty)
            .where(WorkoutFeedback.user_id == user_id)
            .order_by(WorkoutFeedback.created_at.desc())
            .limit(limit)
        )
        return [r[0] for r in result.all()]
