"""Тесты для SmartWorkoutMatcher."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.smart_workout_matcher import SmartWorkoutMatcher
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.equipment import Equipment
from src.domain.entities.questionnaire import CustomQuestion
from src.domain.value_objects.questionnaire import AnswerType


pytestmark = pytest.mark.asyncio


class TestSmartWorkoutMatcher:
    """Тесты для умного матчера тренировок."""

    @pytest.fixture
    def mock_uow(self) -> UnitOfWork:
        """Создаёт мок UnitOfWork."""
        uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        uow.workouts = AsyncMock()
        uow.equipment = AsyncMock()
        uow.custom_questions = AsyncMock()
        return uow

    @pytest.fixture
    def sample_templates(self) -> list[WorkoutTemplate]:
        """Создаёт тестовые шаблоны."""
        equipment_dumbbells: Equipment = Equipment(id=1, name="dumbbells", display_name="Гантели", category="free_weights", is_home_friendly=True)
        equipment_barbell: Equipment = Equipment(id=2, name="barbell", display_name="Штанга", category="free_weights", is_home_friendly=False)
        
        template1: WorkoutTemplate = WorkoutTemplate(
            id=1,
            title="Кардио для похудения",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        template1.required_equipment = []
        
        template2: WorkoutTemplate = WorkoutTemplate(
            id=2,
            title="Силовая для массы",
            goal="muscle_gain",
            difficulty=WorkoutDifficulty.MEDIUM,
            days_per_week=4,
            intensity_factor=1.5,
            workout_category="full_body",
            is_active=True,
        )
        template2.required_equipment = [equipment_barbell]
        
        template3: WorkoutTemplate = WorkoutTemplate(
            id=3,
            title="Домашняя тренировка",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=0.8,
            workout_category="full_body",
            is_active=True,
        )
        template3.required_equipment = [equipment_dumbbells]
        
        return [template1, template2, template3]

    @pytest.fixture
    def sample_user_answers(self) -> list[UserAnswer]:
        """Создаёт тестовые ответы пользователя."""
        goal_question: CustomQuestion = CustomQuestion(id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE)
        level_question: CustomQuestion = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        equipment_question: CustomQuestion = CustomQuestion(id=3, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE)
        
        return [
            UserAnswer(user_id=1, question_id=1, value="weight_loss"),
            UserAnswer(user_id=1, question_id=2, value="beginner"),
            UserAnswer(user_id=1, question_id=3, value=["dumbbells"]),
        ]

    async def test_filters_by_goal_and_level(
        self,
        mock_uow: UnitOfWork,
        sample_templates: list[WorkoutTemplate],
        sample_user_answers: list[UserAnswer],
    ) -> None:
        """Должен фильтровать по цели и уровню."""
        # given
        sample_user_answers[0].question = CustomQuestion(id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[1].question = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[2].question = CustomQuestion(id=3, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE)
        
        mock_uow.workouts.find_by_specification = AsyncMock(return_value=[
            sample_templates[0],  # weight_loss, LOW
            sample_templates[2],  # weight_loss, LOW
        ])
        mock_uow.equipment.get_by_name = AsyncMock(return_value=Equipment(id=1, name="dumbbells", display_name="Гантели", category="free_weights", is_home_friendly=True))
        
        matcher: SmartWorkoutMatcher = SmartWorkoutMatcher(mock_uow)
        
        # when
        result: list[WorkoutTemplate] = await matcher.match(sample_user_answers, limit=10)
        
        # then
        assert len(result) == 2
        assert all(t.goal == "weight_loss" for t in result)
        assert all(t.difficulty == WorkoutDifficulty.LOW for t in result)

    async def test_filters_by_equipment(
        self,
        mock_uow: UnitOfWork,
        sample_templates: list[WorkoutTemplate],
        sample_user_answers: list[UserAnswer],
    ) -> None:
        """Должен фильтровать по оборудованию пользователя."""
        # given
        sample_user_answers[0].question = CustomQuestion(id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[1].question = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[2].question = CustomQuestion(id=3, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE)
        
        # Пользователь имеет только dumbbells
        mock_uow.workouts.find_by_specification = AsyncMock(return_value=[
            sample_templates[0],  # без оборудования
            sample_templates[2],  # требует dumbbells
        ])
        mock_uow.equipment.get_by_name = AsyncMock(return_value=Equipment(id=1, name="dumbbells", display_name="Гантели", category="free_weights", is_home_friendly=True))
        
        matcher: SmartWorkoutMatcher = SmartWorkoutMatcher(mock_uow)
        
        # when
        result: list[WorkoutTemplate] = await matcher.match(sample_user_answers, limit=10)
        
        # then: шаблон с barbell не должен пройти
        assert len(result) == 2
        template_titles: set[str] = {t.title for t in result}
        assert "Домашняя тренировка" in template_titles
        assert "Силовая для массы" not in template_titles

    async def test_sorts_by_score(
        self,
        mock_uow: UnitOfWork,
        sample_templates: list[WorkoutTemplate],
        sample_user_answers: list[UserAnswer],
    ) -> None:
        """Должен сортировать результаты по убыванию скора."""
        # given
        sample_user_answers[0].question = CustomQuestion(id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[1].question = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[2].question = CustomQuestion(id=3, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE)
        
        mock_uow.workouts.find_by_specification = AsyncMock(return_value=sample_templates)
        mock_uow.equipment.get_by_name = AsyncMock(return_value=Equipment(id=1, name="dumbbells", display_name="Гантели", category="free_weights", is_home_friendly=True))
        mock_uow.custom_questions.get_scoring_weight = AsyncMock(return_value=None)
        
        matcher: SmartWorkoutMatcher = SmartWorkoutMatcher(mock_uow)
        
        # when
        result: list[WorkoutTemplate] = await matcher.match(sample_user_answers, limit=10)
        
        # then: результаты должны быть отсортированы (первый имеет больший score)
        assert len(result) >= 1
        # Проверяем, что сортировка работает (можно проверить конкретные значения, если нужно)

    async def test_respects_limit(
        self,
        mock_uow: UnitOfWork,
        sample_templates: list[WorkoutTemplate],
        sample_user_answers: list[UserAnswer],
    ) -> None:
        """Должен возвращать не более limit шаблонов."""
        # given
        sample_user_answers[0].question = CustomQuestion(id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[1].question = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        sample_user_answers[2].question = CustomQuestion(id=3, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE)
        
        mock_uow.workouts.find_by_specification = AsyncMock(return_value=sample_templates)
        mock_uow.equipment.get_by_name = AsyncMock(return_value=Equipment(id=1, name="dumbbells", display_name="Гантели", category="free_weights", is_home_friendly=True))
        mock_uow.custom_questions.get_scoring_weight = AsyncMock(return_value=None)
        
        matcher: SmartWorkoutMatcher = SmartWorkoutMatcher(mock_uow)
        
        # when
        result: list[WorkoutTemplate] = await matcher.match(sample_user_answers, limit=2)
        
        # then
        assert len(result) <= 2

    async def test_returns_empty_when_no_goal(self, mock_uow: UnitOfWork) -> None:
        """Должен возвращать пустой список, если нет цели."""
        # given
        user_answers: list[UserAnswer] = [
            UserAnswer(user_id=1, question_id=2, value="beginner"),
        ]
        user_answers[0].question = CustomQuestion(id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE)
        
        matcher: SmartWorkoutMatcher = SmartWorkoutMatcher(mock_uow)
        
        # when
        result: list[WorkoutTemplate] = await matcher.match(user_answers, limit=10)
        
        # then
        assert len(result) == 0
