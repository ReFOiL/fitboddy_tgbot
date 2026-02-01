from sqlalchemy import select

from src.application.interfaces.repositories import IExerciseRepository
from src.domain.entities.exercise import Exercise
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class ExerciseRepository(SQLAlchemyRepository, IExerciseRepository):
    async def list_all(self) -> list[Exercise]:
        result = await self._session.execute(select(Exercise))
        return list(result.scalars().all())

