"""Тесты для IntensitySpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.specifications import IntensitySpecification
from src.domain.entities.workout import WorkoutTemplate


pytestmark = pytest.mark.asyncio


class TestIntensitySpecification:
    """Тесты для фильтрации по интенсивности."""

    async def test_filters_by_activity_level(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна фильтровать шаблоны по уровню активности."""
        # given: sedentary -> max_intensity = 1.0
        spec: IntensitySpecification = IntensitySpecification("sedentary")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти только шаблоны с intensity_factor <= 1.0
        assert len(templates) == 2
        assert all(t.intensity_factor <= 1.0 for t in templates)

    async def test_filters_moderate_activity(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна фильтровать для умеренной активности."""
        # given: moderate -> max_intensity = 1.5
        spec: IntensitySpecification = IntensitySpecification("moderate")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти шаблоны с intensity_factor <= 1.5
        assert len(templates) == 3
        assert all(t.intensity_factor <= 1.5 for t in templates)

    async def test_filters_active_level(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна фильтровать для активного уровня."""
        # given: active -> max_intensity = 2.0
        spec: IntensitySpecification = IntensitySpecification("active")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти все шаблоны
        assert len(templates) == 4

    async def test_unknown_activity_defaults(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна использовать дефолтное значение для неизвестной активности."""
        # given
        spec: IntensitySpecification = IntensitySpecification("unknown")
        stmt = select(WorkoutTemplate)
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: дефолт = 2.0, должны пройти все
        assert len(templates) == 4
