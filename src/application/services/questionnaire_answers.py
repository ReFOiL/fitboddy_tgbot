from __future__ import annotations

from src.application.services.questionnaire import QuestionnaireService
from src.domain.questionnaire import Question

ValidationValue = str | int | bool | list[str] | None


class QuestionnaireAnswerService:
    def __init__(self, service: QuestionnaireService) -> None:
        self._service = service

    def validate(self, question: Question, text: str) -> tuple[ValidationValue, str | None]:
        return self._service.validate_answer(question, text)

    async def save(self, user_id: int, question: Question, value: ValidationValue) -> bool:
        if value is None:
            return True
        try:
            await self._service.save_answer(
                user_id=user_id,
                question_key=question.key,
                value=value,
            )
        except ValueError:
            return False
        return True
