"""Тесты для EquipmentSpecification."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.specifications import EquipmentSpecification
from src.domain.entities.equipment import Equipment
from src.domain.entities.workout import WorkoutTemplate


pytestmark = pytest.mark.asyncio


class TestEquipmentSpecification:
    """Тесты для фильтрации по оборудованию."""

    async def test_filters_by_user_equipment(
        self,
        db_session: AsyncSession,
        sample_workout_templates: list[WorkoutTemplate],
        sample_equipment: list[Equipment],
    ) -> None:
        """Должна возвращать шаблоны, у которых всё требуемое оборудование есть у пользователя."""
        # given: пользователь имеет dumbbells (id=1)
        user_equipment_ids: list[int] = [sample_equipment[0].id]  # dumbbells
        spec: EquipmentSpecification = EquipmentSpecification(user_equipment_ids)
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти шаблоны без оборудования или с dumbbells
        # Проверяем, что шаблоны с barbell не прошли
        template_titles: set[str] = {t.title for t in templates}
        assert "Домашняя тренировка" in template_titles  # требует dumbbells
        assert "Кардио для похудения" in template_titles  # без оборудования
        assert "Силовая для массы" not in template_titles  # требует barbell

    async def test_filters_multiple_equipment(
        self,
        db_session: AsyncSession,
        sample_workout_templates: list[WorkoutTemplate],
        sample_equipment: list[Equipment],
    ) -> None:
        """Должна работать с несколькими типами оборудования."""
        # given: пользователь имеет dumbbells и barbell
        user_equipment_ids: list[int] = [sample_equipment[0].id, sample_equipment[1].id]
        spec: EquipmentSpecification = EquipmentSpecification(user_equipment_ids)
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти все шаблоны (у пользователя есть всё необходимое)
        assert len(templates) >= 3

    async def test_no_user_equipment(
        self, db_session: AsyncSession, sample_workout_templates: list[WorkoutTemplate]
    ) -> None:
        """Должна возвращать только шаблоны без оборудования, если у пользователя нет оборудования."""
        # given
        spec: EquipmentSpecification = EquipmentSpecification([])
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: должны пройти только шаблоны без оборудования
        assert len(templates) >= 1
        # Проверяем, что все шаблоны без оборудования
        for t in templates:
            assert len(t.required_equipment) == 0

    async def test_excludes_templates_with_missing_equipment(
        self,
        db_session: AsyncSession,
        sample_workout_templates: list[WorkoutTemplate],
        sample_equipment: list[Equipment],
    ) -> None:
        """Должна исключать шаблоны, требующие оборудования, которого нет у пользователя."""
        # given: пользователь имеет только dumbbells, но шаблон требует barbell
        user_equipment_ids: list[int] = [sample_equipment[0].id]  # только dumbbells
        spec: EquipmentSpecification = EquipmentSpecification(user_equipment_ids)
        stmt = select(WorkoutTemplate).options(selectinload(WorkoutTemplate.required_equipment))
        
        # when
        filtered_stmt = spec.apply(stmt)
        result = await db_session.execute(filtered_stmt)
        templates: list[WorkoutTemplate] = list(result.scalars().all())
        
        # then: шаблоны с barbell не должны пройти
        template_titles: set[str] = {t.title for t in templates}
        assert "Силовая для массы" not in template_titles
        assert "Продвинутая силовая" not in template_titles
