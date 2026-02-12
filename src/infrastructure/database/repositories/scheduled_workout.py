from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import IScheduledWorkoutRepository
from src.domain.entities.associations import WorkoutExercise
from src.domain.entities.training_plan import ScheduledWorkout
from src.domain.entities.workout import WorkoutTemplate
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class ScheduledWorkoutRepository(SQLAlchemyRepository, IScheduledWorkoutRepository):
    async def add(self, scheduled: ScheduledWorkout) -> None:
        self._session.add(scheduled)

    async def add_many(self, items: list[ScheduledWorkout]) -> None:
        self._session.add_all(items)

    async def get_by_plan_and_date(self, plan_id: int, on_date: date) -> ScheduledWorkout | None:
        result = await self._session.execute(
            select(ScheduledWorkout)
            .where(
                ScheduledWorkout.plan_id == plan_id,
                ScheduledWorkout.scheduled_for == on_date,
            )
            .options(
                selectinload(ScheduledWorkout.template).selectinload(
                    WorkoutTemplate.workout_exercises
                ).selectinload(WorkoutExercise.exercise)
            )
        )
        return result.scalars().one_or_none()

    async def list_by_plan_id(self, plan_id: int) -> list[ScheduledWorkout]:
        result = await self._session.execute(
            select(ScheduledWorkout)
            .where(ScheduledWorkout.plan_id == plan_id)
            .order_by(ScheduledWorkout.scheduled_for)
        )
        return list(result.scalars().all())

    async def mark_completed(self, scheduled_id: int) -> None:
        await self._session.execute(
            update(ScheduledWorkout)
            .where(ScheduledWorkout.id == scheduled_id)
            .values(is_completed=True, completed_at=datetime.now(timezone.utc))
        )
