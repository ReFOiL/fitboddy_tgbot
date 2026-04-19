"""Тесты для AndSpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.specifications import AndSpecification, GoalSpecification, DifficultySpecification
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


pytestmark = pytest.mark.asyncio


class TestAndSpecification:
    """Тесты для комбинирования спецификаций через AND."""

    async def test_combines_two_specifications(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна комбинировать две спецификации через AND."""
        # given
        goal_spec: GoalSpecification = GoalSpecification("weight_loss")
        difficulty_spec: DifficultySpecification = DifficultySpecification("beginner")
        combined: AndSpecification = AndSpecification(goal_spec, difficulty_spec)
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = combined.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти только шаблоны с goal=weight_loss И difficulty=LOW
        assert len(templates) == 2
        assert all(t.goal == "weight_loss" for t in templates)
        assert all(t.difficulty == WorkoutDifficulty.LOW for t in templates)

    async def test_combines_three_specifications(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна комбинировать три спецификации."""
        # given
        goal_spec: GoalSpecification = GoalSpecification("muscle_gain")
        difficulty_spec: DifficultySpecification = DifficultySpecification("intermediate")
        # Добавим IntensitySpecification
        from src.application.specifications import IntensitySpecification
        intensity_spec: IntensitySpecification = IntensitySpecification("moderate")
        combined: AndSpecification = AndSpecification(goal_spec, difficulty_spec, intensity_spec)
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = combined.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти шаблоны, соответствующие всем трём условиям
        assert len(templates) == 1
        assert templates[0].goal == "muscle_gain"
        assert templates[0].difficulty == WorkoutDifficulty.MEDIUM
        assert templates[0].intensity_factor <= 1.5

    async def test_no_matches_when_conditions_conflict(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать пустой список, если условия конфликтуют."""
        # given: goal=weight_loss И difficulty=HIGH (но у нас нет таких шаблонов)
        goal_spec: GoalSpecification = GoalSpecification("weight_loss")
        difficulty_spec: DifficultySpecification = DifficultySpecification("advanced")
        combined: AndSpecification = AndSpecification(goal_spec, difficulty_spec)
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = combined.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 0
