from __future__ import annotations

from src.application.services.questionnaire import Question, QuestionnaireService


class QuestionnaireFlowQueries:
    def __init__(self, service: QuestionnaireService) -> None:
        self._service = service

    async def next_question(self, user_id: int) -> tuple[Question | None, bool]:
        return await self._service.get_next_question(user_id)

    async def question_by_key(self, key: str) -> Question | None:
        return await self._service.get_question_by_key(key)

    async def ordered_keys(self) -> list[str]:
        return await self._service.get_ordered_keys()
