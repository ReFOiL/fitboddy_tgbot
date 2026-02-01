from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.questionnaire import CustomQuestion
from src.domain.entities.user_answer import UserAnswer
from src.domain.questionnaire import AnswerValidator, Question, QuestionFactory
from src.domain.value_objects.questionnaire import AnswerType


class QuestionnaireService:
    def __init__(
        self,
        uow: UnitOfWork,
        validator: AnswerValidator | None = None,
        factory: QuestionFactory | None = None,
    ) -> None:
        self.uow = uow
        self._validator = validator or AnswerValidator()
        self._factory = factory or QuestionFactory()

    async def get_next_question(
        self,
        user_id: int,
        current_state: str | None = None,
    ) -> tuple[Question | None, bool]:
        async with self.uow:
            answered_keys = await self.uow.user_answers.get_answered_keys(user_id)
            questions = await self.uow.custom_questions.list_active_ordered()
            for question in questions:
                if question.key not in answered_keys:
                    return self._factory.from_entity(question), False
        return None, True

    async def get_question_by_key(self, question_key: str) -> Question | None:
        async with self.uow:
            question = await self.uow.custom_questions.get_by_key(question_key)
        if question is None:
            return None
        return self._factory.from_entity(question)

    async def get_ordered_keys(self) -> list[str]:
        async with self.uow:
            questions = await self.uow.custom_questions.list_active_ordered()
        return [question.key for question in questions]

    async def save_answer(self, user_id: int, question_key: str, value: str | int | bool | list[str] | None) -> None:
        async with self.uow:
            question = await self.uow.custom_questions.get_by_key(question_key)
            if question is None:
                raise ValueError("Question not found")
            await self.uow.user_answers.delete_by_question(user_id, question.id)
            answers = self._build_answers(user_id, question, value)
            if answers:
                await self.uow.user_answers.add_many(answers)
            await self.uow.commit()

    def validate_answer(
        self,
        question: Question,
        text: str,
    ) -> tuple[str | int | bool | list[str] | None, str | None]:
        return self._validator.validate(question, text)

    def _build_answers(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        if value is None:
            return []
        if question.answer_type in {AnswerType.SINGLE_CHOICE, AnswerType.MULTIPLE_CHOICE}:
            options_by_value = {opt.value: opt.id for opt in question.options}
            if question.answer_type == AnswerType.MULTIPLE_CHOICE:
                if not isinstance(value, list):
                    return []
                answers: list[UserAnswer] = []
                for item in value:
                    option_id = options_by_value.get(str(item))
                    if option_id is None:
                        continue
                    answers.append(
                        UserAnswer(user_id=user_id, question_id=question.id, option_id=option_id)
                    )
                return answers
            option_id = options_by_value.get(str(value))
            if option_id is None:
                return []
            return [UserAnswer(user_id=user_id, question_id=question.id, option_id=option_id)]
        return [UserAnswer(user_id=user_id, question_id=question.id, value=value)]
