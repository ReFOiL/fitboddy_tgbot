from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import IWorkoutTemplateRepository
from src.domain.entities.associations import WorkoutExercise
from src.domain.entities.workout import WorkoutTemplate
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class WorkoutTemplateRepository(SQLAlchemyRepository, IWorkoutTemplateRepository):
    async def list_all(self) -> list[WorkoutTemplate]:
        result = await self._session.execute(
            select(WorkoutTemplate)
            .options(
                selectinload(WorkoutTemplate.workout_exercises).selectinload(WorkoutExercise.exercise)
            )
            .order_by(WorkoutTemplate.title)
        )
        return list(result.scalars().all())

    async def get_by_id(self, template_id: int) -> WorkoutTemplate | None:
        result = await self._session.execute(
            select(WorkoutTemplate)
            .where(WorkoutTemplate.id == template_id)
            .options(
                selectinload(WorkoutTemplate.workout_exercises).selectinload(WorkoutExercise.exercise)
            )
        )
        return result.scalars().one_or_none()

    async def add(self, template: WorkoutTemplate) -> None:
        self._session.add(template)

    async def delete(self, template_id: int) -> None:
        await self._session.execute(delete(WorkoutTemplate).where(WorkoutTemplate.id == template_id))

