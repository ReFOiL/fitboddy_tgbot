from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import IScheduledWorkoutRepository
from src.domain.entities.training_plan import ScheduledWorkout, ScheduledWorkoutExercise
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


def _session_load_options():
    return (
        selectinload(ScheduledWorkout.plan),
        selectinload(ScheduledWorkout.session_exercises).selectinload(ScheduledWorkoutExercise.exercise),
    )


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
            .options(*_session_load_options())
        )
        return result.scalars().one_or_none()

    async def list_by_plan_id(self, plan_id: int) -> list[ScheduledWorkout]:
        result = await self._session.execute(
            select(ScheduledWorkout)
            .where(ScheduledWorkout.plan_id == plan_id)
            .order_by(ScheduledWorkout.scheduled_for)
            .options(*_session_load_options())
        )
        return list(result.scalars().all())

    async def get_by_id(self, scheduled_id: int) -> ScheduledWorkout | None:
        result = await self._session.execute(
            select(ScheduledWorkout).where(ScheduledWorkout.id == scheduled_id).options(*_session_load_options())
        )
        return result.scalars().one_or_none()

    async def mark_completed(self, scheduled_id: int) -> None:
        await self._session.execute(
            update(ScheduledWorkout)
            .where(ScheduledWorkout.id == scheduled_id)
            .values(is_completed=True, completed_at=datetime.now(timezone.utc))
        )

    async def set_perceived_effort(self, scheduled_id: int, effort: str) -> None:
        await self._session.execute(
            update(ScheduledWorkout)
            .where(ScheduledWorkout.id == scheduled_id)
            .values(perceived_effort=effort)
        )

    async def has_other_on_plan_date(
        self, plan_id: int, on_date: date, exclude_scheduled_id: int
    ) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(ScheduledWorkout)
            .where(
                ScheduledWorkout.plan_id == plan_id,
                ScheduledWorkout.scheduled_for == on_date,
                ScheduledWorkout.id != exclude_scheduled_id,
            )
        )
        n = result.scalar_one()
        return int(n or 0) > 0

    async def delete_session_exercises(self, scheduled_workout_id: int) -> None:
        await self._session.execute(
            delete(ScheduledWorkoutExercise).where(
                ScheduledWorkoutExercise.scheduled_workout_id == scheduled_workout_id
            )
        )
