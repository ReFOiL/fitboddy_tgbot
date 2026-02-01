from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import IUserAnswerRepository
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.questionnaire import CustomQuestion
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class UserAnswerRepository(SQLAlchemyRepository, IUserAnswerRepository):
    async def get_answered_keys(self, user_id: int) -> set[str]:
        result = await self._session.execute(
            select(CustomQuestion.key)
            .join(UserAnswer, UserAnswer.question_id == CustomQuestion.id)
            .where(UserAnswer.user_id == user_id)
        )
        return {row[0] for row in result.all() if row[0]}

    async def list_by_user_id(self, user_id: int) -> list[UserAnswer]:
        result = await self._session.execute(
            select(UserAnswer)
            .where(UserAnswer.user_id == user_id)
            .options(
                selectinload(UserAnswer.question),
                selectinload(UserAnswer.option),
            )
        )
        return list(result.scalars().all())

    async def delete_by_question(self, user_id: int, question_id: int) -> None:
        await self._session.execute(
            delete(UserAnswer).where(
                UserAnswer.user_id == user_id, UserAnswer.question_id == question_id
            )
        )

    async def add_many(self, answers: list[UserAnswer]) -> None:
        self._session.add_all(answers)
