"""Тесты для GoalSpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.specifications import GoalSpecification
from src.domain.entities.workout import WorkoutTemplate


pytestmark = pytest.mark.asyncio


class TestGoalSpecification:
    """Тесты для фильтрации по цели тренировки."""

    async def test_filters_by_goal(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна фильтровать шаблоны по target_goal."""
        # given
        spec: GoalSpecification = GoalSpecification("weight_loss")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 2
        assert all(t.goal == "weight_loss" for t in templates)
        assert all(t.title in ["Кардио для похудения", "Домашняя тренировка"] for t in templates)

    async def test_filters_different_goal(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна фильтровать по другой цели."""
        # given
        spec: GoalSpecification = GoalSpecification("muscle_gain")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 2
        assert all(t.goal == "muscle_gain" for t in templates)

    async def test_no_matches(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать пустой список, если нет совпадений."""
        # given
        spec: GoalSpecification = GoalSpecification("endurance")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 0
