from sqlalchemy import delete, select

from src.application.interfaces.repositories import IExerciseRepository
from src.domain.entities.exercise import Exercise
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class ExerciseRepository(SQLAlchemyRepository, IExerciseRepository):
    async def list_all(self) -> list[Exercise]:
        result = await self._session.execute(select(Exercise).order_by(Exercise.name))
        return list(result.scalars().all())

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        result = await self._session.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalars().one_or_none()

    async def get_by_name(self, name: str) -> Exercise | None:
        result = await self._session.execute(select(Exercise).where(Exercise.name == name))
        return result.scalars().one_or_none()

    async def add(self, exercise: Exercise) -> None:
        self._session.add(exercise)

    async def delete(self, exercise_id: int) -> None:
        await self._session.execute(delete(Exercise).where(Exercise.id == exercise_id))

