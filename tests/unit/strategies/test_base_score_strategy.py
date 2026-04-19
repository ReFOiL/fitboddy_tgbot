"""Тесты для BaseScoreStrategy."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.application.interfaces.repositories import UnitOfWork
from src.application.strategies import BaseScoreStrategy
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


pytestmark = pytest.mark.asyncio


class TestBaseScoreStrategy:
    """Тесты для базовой стратегии скоринга."""

    async def test_returns_base_score(self) -> None:
        """Должен возвращать базовый score для всех шаблонов."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="cardio",
        )
        user_answers: list[UserAnswer] = []
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        strategy: BaseScoreStrategy = BaseScoreStrategy(base_score=100)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then
        assert score == 100

    async def test_custom_base_score(self) -> None:
        """Должен использовать кастомное значение base_score."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="cardio",
        )
        user_answers: list[UserAnswer] = []
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        strategy: BaseScoreStrategy = BaseScoreStrategy(base_score=50)
        
        # when
        score: int = await strategy.calculate(template, user_answers, mock_uow)
        
        # then
        assert score == 50
