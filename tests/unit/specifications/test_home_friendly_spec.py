"""Тесты для HomeFriendlySpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.specifications import HomeFriendlySpecification
from src.domain.entities.equipment import Equipment
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


pytestmark = pytest.mark.asyncio


class TestHomeFriendlySpecification:
    """Тесты для фильтрации домашних тренировок."""

    async def test_filters_home_friendly_equipment(
        self, db_session: AsyncSession, sample_equipment: list[Equipment]
    ) -> None:
        """Должна возвращать только шаблоны с домашним оборудованием или без оборудования."""
        # given: создаём шаблоны с разным оборудованием
        template_home: WorkoutTemplate = WorkoutTemplate(
            title="Домашняя",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
            is_active=True,
        )
        template_home.required_equipment = [sample_equipment[0]]  # dumbbells (home friendly)
        
        template_gym: WorkoutTemplate = WorkoutTemplate(
            title="Заловая",
            goal="muscle_gain",
            difficulty=WorkoutDifficulty.MEDIUM,
            days_per_week=4,
            intensity_factor=1.5,
            workout_category="full_body",
            is_active=True,
        )
        template_gym.required_equipment = [sample_equipment[1]]  # barbell (not home friendly)
        
        template_no_equipment: WorkoutTemplate = WorkoutTemplate(
            title="Без оборудования",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        template_no_equipment.required_equipment = []
        
        db_session.add_all([template_home, template_gym, template_no_equipment])
        await db_session.flush()
        
        # when
        spec: HomeFriendlySpecification = HomeFriendlySpecification([])
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти только домашние и без оборудования
        template_titles: set[str] = {t.title for t in templates}
        assert "Домашняя" in template_titles
        assert "Без оборудования" in template_titles
        assert "Заловая" not in template_titles
        
        # Проверяем, что все прошедшие шаблоны действительно домашние
        for t in templates:
            if t.required_equipment:
                assert all(eq.is_home_friendly for eq in t.required_equipment)
