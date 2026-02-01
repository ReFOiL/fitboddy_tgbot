from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import ICustomQuestionRepository
from src.domain.entities.questionnaire import CustomQuestion
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class CustomQuestionRepository(SQLAlchemyRepository, ICustomQuestionRepository):
    async def list_active(self) -> list[CustomQuestion]:
        result = await self._session.execute(
            select(CustomQuestion).where(CustomQuestion.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_active_ordered(self) -> list[CustomQuestion]:
        result = await self._session.execute(
            select(CustomQuestion)
            .where(CustomQuestion.is_active.is_(True))
            .order_by(CustomQuestion.order)
            .options(selectinload(CustomQuestion.options))
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[CustomQuestion]:
        result = await self._session.execute(
            select(CustomQuestion)
            .order_by(CustomQuestion.order)
            .options(selectinload(CustomQuestion.options))
        )
        return list(result.scalars().all())

    async def get(self, question_id: int) -> CustomQuestion | None:
        result = await self._session.execute(
            select(CustomQuestion)
            .where(CustomQuestion.id == question_id)
            .options(selectinload(CustomQuestion.options))
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> CustomQuestion | None:
        result = await self._session.execute(
            select(CustomQuestion)
            .where(CustomQuestion.key == key)
            .options(selectinload(CustomQuestion.options))
        )
        return result.scalar_one_or_none()

    async def add(self, question: CustomQuestion) -> None:
        self._session.add(question)
