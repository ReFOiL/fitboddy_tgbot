"""Тесты для DifficultySpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.specifications import DifficultySpecification
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


pytestmark = pytest.mark.asyncio


class TestDifficultySpecification:
    """Тесты для фильтрации по уровню сложности."""

    async def test_filters_beginner(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать только LOW для beginner."""
        # given
        spec: DifficultySpecification = DifficultySpecification("beginner")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 2
        assert all(t.difficulty == WorkoutDifficulty.LOW for t in templates)

    async def test_filters_intermediate(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать LOW и MEDIUM для intermediate."""
        # given
        spec: DifficultySpecification = DifficultySpecification("intermediate")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 3
        assert all(t.difficulty in [WorkoutDifficulty.LOW, WorkoutDifficulty.MEDIUM] for t in templates)

    async def test_filters_advanced(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать MEDIUM и HIGH для advanced."""
        # given
        spec: DifficultySpecification = DifficultySpecification("advanced")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 2
        assert all(t.difficulty in [WorkoutDifficulty.MEDIUM, WorkoutDifficulty.HIGH] for t in templates)

    async def test_unknown_level_defaults(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать все уровни для неизвестного уровня."""
        # given
        spec: DifficultySpecification = DifficultySpecification("unknown")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 4  # Все шаблоны
