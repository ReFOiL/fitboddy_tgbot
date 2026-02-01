from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.interfaces.repositories import UnitOfWork
from src.infrastructure.database.repositories.exercise import ExerciseRepository
from src.infrastructure.database.repositories.payment import PaymentRepository
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.repositories.custom_question import CustomQuestionRepository
from src.infrastructure.database.repositories.question_template_link import QuestionTemplateLinkRepository
from src.infrastructure.database.repositories.user_answer import UserAnswerRepository
from src.infrastructure.database.repositories.workout import WorkoutTemplateRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = UserRepository(self._session)
        self.exercises = ExerciseRepository(self._session)
        self.workouts = WorkoutTemplateRepository(self._session)
        self.payments = PaymentRepository(self._session)
        self.custom_questions = CustomQuestionRepository(self._session)
        self.user_answers = UserAnswerRepository(self._session)
        self.question_template_links = QuestionTemplateLinkRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self._session:
            return
        if exc:
            await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()

