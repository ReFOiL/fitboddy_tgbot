from __future__ import annotations

from sqlalchemy import delete, select

from src.application.interfaces.repositories import IWorkoutReflectionRepository
from src.domain.entities.workout_reflection import WorkoutReflection
from src.domain.value_objects.workout_profile import ReflectionEnergy
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class WorkoutReflectionRepository(SQLAlchemyRepository, IWorkoutReflectionRepository):
    async def upsert(
        self, user_id: int, scheduled_workout_id: int, energy: ReflectionEnergy
    ) -> None:
        await self._session.execute(
            delete(WorkoutReflection).where(
                WorkoutReflection.user_id == user_id,
                WorkoutReflection.scheduled_workout_id == scheduled_workout_id,
            )
        )
        self._session.add(
            WorkoutReflection(
                user_id=user_id,
                scheduled_workout_id=scheduled_workout_id,
                energy=str(energy),
            )
        )
        await self._session.flush()

    async def list_last_energy_levels(
        self, user_id: int, *, limit: int = 5
    ) -> list[ReflectionEnergy]:
        result = await self._session.execute(
            select(WorkoutReflection.energy)
            .where(WorkoutReflection.user_id == user_id)
            .order_by(WorkoutReflection.created_at.desc())
            .limit(limit)
        )
        out: list[ReflectionEnergy] = []
        for row in result.all():
            parsed = ReflectionEnergy.from_raw(row[0])
            if parsed is not None:
                out.append(parsed)
        return out

