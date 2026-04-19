from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import IWorkoutTemplateRepository
from src.application.specifications import Specification
from src.domain.entities.associations import WorkoutExercise
from src.domain.entities.workout import WorkoutTemplate
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class WorkoutTemplateRepository(SQLAlchemyRepository, IWorkoutTemplateRepository):
    async def list_all(self) -> list[WorkoutTemplate]:
        result = await self._session.execute(
            select(WorkoutTemplate)
            .options(
                selectinload(WorkoutTemplate.workout_exercises).selectinload(WorkoutExercise.exercise),
                selectinload(WorkoutTemplate.required_equipment),
            )
            .order_by(WorkoutTemplate.title)
        )
        return list(result.scalars().all())

    async def get_by_id(self, template_id: int) -> WorkoutTemplate | None:
        result = await self._session.execute(
            select(WorkoutTemplate)
            .where(WorkoutTemplate.id == template_id)
            .options(
                selectinload(WorkoutTemplate.workout_exercises).selectinload(WorkoutExercise.exercise),
                selectinload(WorkoutTemplate.required_equipment),
            )
        )
        return result.scalars().one_or_none()

    async def add(self, template: WorkoutTemplate) -> None:
        self._session.add(template)

    async def delete(self, template_id: int) -> None:
        await self._session.execute(delete(WorkoutTemplate).where(WorkoutTemplate.id == template_id))

    async def find_by_specification(self, specification: Specification) -> list[WorkoutTemplate]:
        """Найти шаблоны по спецификации с предзагрузкой связей."""
        stmt = (
            select(WorkoutTemplate)
            .options(
                selectinload(WorkoutTemplate.workout_exercises).selectinload(WorkoutExercise.exercise),
                selectinload(WorkoutTemplate.required_equipment),
                # Примечание: allowed_genders больше не relationship, хранится как строки в workout_template_allowed_genders
                selectinload(WorkoutTemplate.linked_questions),
            )
            .where(WorkoutTemplate.is_active.is_(True))
        )
        stmt = specification.apply(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

