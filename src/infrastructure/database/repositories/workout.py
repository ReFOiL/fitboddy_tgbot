from sqlalchemy import select

from src.application.interfaces.repositories import IWorkoutTemplateRepository
from src.domain.entities.workout import WorkoutTemplate
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class WorkoutTemplateRepository(SQLAlchemyRepository, IWorkoutTemplateRepository):
    async def list_all(self) -> list[WorkoutTemplate]:
        result = await self._session.execute(select(WorkoutTemplate))
        return list(result.scalars().all())

    async def add(self, template: WorkoutTemplate) -> None:
        self._session.add(template)

