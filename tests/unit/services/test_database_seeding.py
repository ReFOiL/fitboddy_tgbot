"""Тесты для проверки корректности наполнения БД тестовыми данными."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.equipment import Equipment
from src.domain.entities.workout import WorkoutTemplate


pytestmark = pytest.mark.asyncio


class TestDatabaseSeeding:
    """Тесты для проверки наполнения БД."""

    async def test_equipment_seeded(
        self, db_session: AsyncSession, sample_equipment: list[Equipment]
    ) -> None:
        """Проверяет, что оборудование корректно создано в БД."""
        # when
        result = await db_session.execute(select(Equipment))
        equipment_list: list[Equipment] = list(result.scalars().all())
        
        # then
        assert len(equipment_list) == 4
        equipment_names: set[str] = {e.name for e in equipment_list}
        assert "dumbbells" in equipment_names
        assert "barbell" in equipment_names
        assert "none" in equipment_names
        assert "resistance_bands" in equipment_names

    async def test_workout_templates_have_equipment_relations(
        self,
        db_session: AsyncSession,
        sample_workout_templates: list[WorkoutTemplate],
        sample_equipment: list[Equipment],
    ) -> None:
        """Проверяет, что шаблоны корректно связаны с оборудованием."""
        # when - загружаем шаблоны с оборудованием через selectinload
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        result = await db_session.execute(stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # Находим нужные шаблоны
        home_template: WorkoutTemplate | None = next((t for t in templates if "Домашняя" in t.title), None)
        strength_template: WorkoutTemplate | None = next((t for t in templates if "Силовая" in t.title), None)
        
        # then
        assert home_template is not None
        assert len(home_template.required_equipment) == 1
        assert home_template.required_equipment[0].name == "dumbbells"
        
        assert strength_template is not None
        assert len(strength_template.required_equipment) == 1
        assert strength_template.required_equipment[0].name == "barbell"

    async def test_workout_templates_have_new_fields(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Проверяет, что шаблоны имеют новые поля."""
        # when
        template: WorkoutTemplate = sample_workout_templates[0]
        
        # then
        assert hasattr(template, "intensity_factor")
        assert hasattr(template, "workout_category")
        assert hasattr(template, "min_age")
        assert hasattr(template, "max_age")
        assert template.intensity_factor == 1.0
        assert template.workout_category == "cardio"
