"""Тесты для CompositeScoringStrategy."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.application.interfaces.repositories import UnitOfWork
from src.application.strategies import (
    CompositeScoringStrategy,
    BaseScoreStrategy,
    EquipmentOverlapScoring,
    CustomQuestionScoring,
)
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty
from src.domain.entities.user_answer import UserAnswer


pytestmark = pytest.mark.asyncio


class TestCompositeScoringStrategy:
    """Тесты для композитной стратегии скоринга."""

    async def test_aggregates_multiple_strategies(self) -> None:
        """Должна агрегировать несколько стратегий с весами."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        user_answers: list[UserAnswer] = []
        
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        
        # Создаём моки стратегий
        base_strategy: BaseScoreStrategy = BaseScoreStrategy(base_score=100)
        equipment_strategy: EquipmentOverlapScoring = EquipmentOverlapScoring(points_per_match=10)
        custom_strategy: CustomQuestionScoring = CustomQuestionScoring(default_weight=5)
        
        # Мокаем результаты стратегий
        async def mock_equipment_calc(
            template: WorkoutTemplate, user_answers: list[UserAnswer], uow: UnitOfWork
        ) -> int:
            return 20
        
        async def mock_custom_calc(
            template: WorkoutTemplate, user_answers: list[UserAnswer], uow: UnitOfWork
        ) -> int:
            return 15
        
        equipment_strategy.calculate = mock_equipment_calc
        custom_strategy.calculate = mock_custom_calc
        
        composite: CompositeScoringStrategy = CompositeScoringStrategy([
            (base_strategy, 1),
            (equipment_strategy, 2),
            (custom_strategy, 1),
        ])
        
        # when
        score: int = await composite.calculate(template, user_answers, mock_uow)
        
        # then: 100*1 + 20*2 + 15*1 = 100 + 40 + 15 = 155
        assert score == 155

    async def test_handles_zero_weights(self) -> None:
        """Должна корректно обрабатывать нулевые веса."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        user_answers: list[UserAnswer] = []
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        
        base_strategy: BaseScoreStrategy = BaseScoreStrategy(base_score=100)
        equipment_strategy: EquipmentOverlapScoring = EquipmentOverlapScoring(points_per_match=10)
        
        async def mock_equipment_calc(
            template: WorkoutTemplate, user_answers: list[UserAnswer], uow: UnitOfWork
        ) -> int:
            return 20
        
        equipment_strategy.calculate = mock_equipment_calc
        
        composite: CompositeScoringStrategy = CompositeScoringStrategy([
            (base_strategy, 0),  # Нулевой вес
            (equipment_strategy, 1),
        ])
        
        # when
        score: int = await composite.calculate(template, user_answers, mock_uow)
        
        # then: 100*0 + 20*1 = 20
        assert score == 20

    async def test_single_strategy(self) -> None:
        """Должна работать с одной стратегией."""
        # given
        template: WorkoutTemplate = WorkoutTemplate(
            title="Тест",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
        )
        user_answers: list[UserAnswer] = []
        mock_uow: UnitOfWork = AsyncMock(spec=UnitOfWork)
        
        base_strategy: BaseScoreStrategy = BaseScoreStrategy(base_score=100)
        composite: CompositeScoringStrategy = CompositeScoringStrategy([
            (base_strategy, 1),
        ])
        
        # when
        score: int = await composite.calculate(template, user_answers, mock_uow)
        
        # then
        assert score == 100
