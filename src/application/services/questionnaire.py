from __future__ import annotations

from src.application.factories.answer_builder_factory import AnswerBuilderFactory
from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.user_answer import UserAnswer
from src.domain.questionnaire import AnswerValidator, Question, QuestionFactory
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import WorkoutLocation
from src.shared.utils.profile_answers import AnswerLookup


class QuestionnaireService:
    def __init__(
        self,
        uow: UnitOfWork,
        validator: AnswerValidator | None = None,
        factory: QuestionFactory | None = None,
        answer_builder_factory: AnswerBuilderFactory | None = None,
    ) -> None:
        self.uow = uow
        self._validator = validator or AnswerValidator()
        self._factory = factory or QuestionFactory()
        self._answer_builder_factory = answer_builder_factory or AnswerBuilderFactory()

    async def get_next_question(
        self,
        user_id: int,
        current_state: str | None = None,
    ) -> tuple[Question | None, bool]:
        async with self.uow:
            answered_keys = await self.uow.user_answers.get_answered_keys(user_id)
            answers = await self.uow.user_answers.list_by_user_id(user_id)
            questions = await self.uow.custom_questions.list_active_ordered()
            for question in questions:
                if self._should_skip_question(question.key, answers):
                    continue
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
            user = await self.uow.users.get_by_id(user_id)
            if user is None:
                raise ValueError("User not found")
            
            # Все вопросы (системные и кастомные) сохраняем в UserAnswer
            question = await self.uow.custom_questions.get_by_key(question_key)
            if question is None:
                raise ValueError("Question not found")
            
            await self.uow.user_answers.delete_by_question(user_id, question.id)
            answers = self._answer_builder_factory.build_answers(user_id, question, value)
            if answers:
                await self.uow.user_answers.add_many(answers)
            
            # Все данные профиля хранятся только в UserAnswer - единый источник истины!
            # Никакой синхронизации не требуется.
            
            await self.uow.commit()

    def validate_answer(
        self,
        question: Question,
        text: str,
    ) -> tuple[str | int | bool | list[str] | None, str | None]:
        return self._validator.validate(question, text)

    @staticmethod
    def _should_skip_question(question_key: str, user_answers: list[UserAnswer]) -> bool:
        if question_key != SystemQuestionKey.EQUIPMENT:
            return False
        location_raw = AnswerLookup(user_answers).get_str(SystemQuestionKey.WORKOUT_LOCATION)
        return WorkoutLocation.from_raw(location_raw) == WorkoutLocation.GYM
