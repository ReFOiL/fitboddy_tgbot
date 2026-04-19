"""Тесты для AgeSpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.specifications import AgeSpecification
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


pytestmark = pytest.mark.asyncio


class TestAgeSpecification:
    """Тесты для фильтрации по возрасту."""

    async def test_filters_by_age_within_range(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать шаблоны, у которых возраст пользователя входит в диапазон."""
        # given: создаём шаблоны с ограничениями по возрасту
        template_with_age: WorkoutTemplate = WorkoutTemplate(
            title="Для молодых",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            min_age=18,
            max_age=30,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        template_no_age: WorkoutTemplate = WorkoutTemplate(
            title="Для всех",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            min_age=None,
            max_age=None,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        db_session.add_all([template_with_age, template_no_age])
        await db_session.flush()
        
        # when: пользователь 25 лет
        spec: AgeSpecification = AgeSpecification(25)
        stmt = select(WorkoutTemplate)
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти оба шаблона
        template_titles: set[str] = {t.title for t in templates}
        assert "Для молодых" in template_titles
        assert "Для всех" in template_titles

    async def test_excludes_age_out_of_range(self, db_session: AsyncSession) -> None:
        """Должна исключать шаблоны, если возраст вне диапазона."""
        # given
        template_young: WorkoutTemplate = WorkoutTemplate(
            title="Для молодых",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            min_age=18,
            max_age=30,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        template_old: WorkoutTemplate = WorkoutTemplate(
            title="Для пожилых",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            min_age=50,
            max_age=70,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        db_session.add_all([template_young, template_old])
        await db_session.flush()
        
        # when: пользователь 40 лет
        spec: AgeSpecification = AgeSpecification(40)
        stmt = select(WorkoutTemplate)
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: оба шаблона должны быть исключены
        template_titles: set[str] = {t.title for t in templates}
        assert "Для молодых" not in template_titles
        assert "Для пожилых" not in template_titles

    async def test_allows_templates_without_age_restrictions(self, db_session: AsyncSession) -> None:
        """Должна разрешать шаблоны без ограничений по возрасту."""
        # given
        template_no_age: WorkoutTemplate = WorkoutTemplate(
            title="Для всех",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            min_age=None,
            max_age=None,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        )
        db_session.add(template_no_age)
        await db_session.flush()
        
        # when: любой возраст
        spec: AgeSpecification = AgeSpecification(99)
        stmt = select(WorkoutTemplate)
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then
        assert len(templates) == 1
        assert templates[0].title == "Для всех"
