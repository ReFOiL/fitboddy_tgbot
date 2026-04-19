"""Тесты для CustomQuestionScoring."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.application.interfaces.repositories import UnitOfWork
from src.application.strategies import CustomQuestionScoring
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType


pytestmark = pytest.mark.asyncio


class TestCustomQuestionScoring:
    """Тесты для скоринга по кастомным вопросам."""

    async def test_calculates_score_from_weights(self) -> None:
        """Должен рассчитывать score на основе весов из таблицы."""
        # given
        question1: CustomQuestion = CustomQuestion(
            id=1,
            key="custom:preferred_time",
            text="Предпочитаемое время",
            answer_type=AnswerType.SINGLE_CHOICE,
        )
        question2: CustomQuestion = CustomQuestion(
            id=2,
            key="custom:stress_level",
            text="Уровень стресса",
            answer_type=AnswerType.NUMBER,
        )
        
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        template.linked_questions = [question1, question2]
        
        user_answers: list[UserAnswer] = [
            UserAnswer(
                user_id=1,
                question_id=1,
                value="morning",
                option=CustomQuestionOption(id=1, question_id=1, value="morning", label="Утро", sort_order=1),
            ),
            UserAnswer(
                user_id=1,
                question_id=2,
                value=5,
            ),
        ]
        user_answers[0].question = question1
        user_answers[1].question = question2
        
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        mock_uow.custom_questions = AsyncMock()
        async def get_scoring_weight(q_id: int, val: str) -> int:
            weights_map: dict[tuple[int, str], int] = {
                (1, "morning"): 20,
                (2, "5"): -5,
            }
            return weights_map.get((q_id, val), 0)
        mock_uow.custom_questions.get_scoring_weight = AsyncMock(side_effect=get_scoring_weight)
        
        strategy: CustomQuestionScoring = CustomQuestionScoring(default_weight=0)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then: 20 + (-5) = 15
        assert score == 15

    async def test_uses_default_weight_when_not_found(self) -> None:
        """Должен использовать default_weight, если вес не найден."""
        # given
        question1: CustomQuestion = CustomQuestion(
            id=1,
            key="custom:preferred_time",
            text="Предпочитаемое время",
            answer_type=AnswerType.SINGLE_CHOICE,
        )
        
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        template.linked_questions = [question1]
        
        user_answers: list[UserAnswer] = [
            UserAnswer(
                user_id=1,
                question_id=1,
                value="afternoon",
            )
        ]
        user_answers[0].question = question1
        
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        mock_uow.custom_questions = AsyncMock()
        mock_uow.custom_questions.get_scoring_weight = AsyncMock(return_value=None)
        
        strategy: CustomQuestionScoring = CustomQuestionScoring(default_weight=10)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then: используется default_weight
        assert score == 10

    async def test_returns_zero_for_no_linked_questions(self) -> None:
        """Должен возвращать 0, если нет привязанных вопросов."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        template.linked_questions = []
        
        user_answers: list[UserAnswer] = []
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        strategy: CustomQuestionScoring = CustomQuestionScoring(default_weight=0)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then
        assert score == 0

    async def test_handles_missing_user_answer(self) -> None:
        """Должен корректно обрабатывать отсутствие ответа пользователя."""
        # given
        question1: CustomQuestion = CustomQuestion(
            id=1,
            key="custom:preferred_time",
            text="Предпочитаемое время",
            answer_type=AnswerType.SINGLE_CHOICE,
        )
        
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        template.linked_questions = [question1]
        
        # Пользователь не ответил на этот вопрос
        user_answers: list[UserAnswer] = []
        
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        strategy: CustomQuestionScoring = CustomQuestionScoring(default_weight=0)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then: score = 0, так как нет ответа
        assert score == 0
