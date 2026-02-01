from sqlalchemy import insert, select

from src.application.interfaces.repositories import IQuestionTemplateLinkRepository
from src.domain.entities.questionnaire import question_template_links
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class QuestionTemplateLinkRepository(SQLAlchemyRepository, IQuestionTemplateLinkRepository):
    async def add(self, question_id: int, template_id: int) -> None:
        await self._session.execute(
            insert(question_template_links).values(
                question_id=question_id,
                template_id=template_id,
            )
        )

    async def list_all(self) -> list[tuple[int, int]]:
        result = await self._session.execute(
            select(question_template_links.c.question_id, question_template_links.c.template_id)
        )
        return [(row[0], row[1]) for row in result.all()]
