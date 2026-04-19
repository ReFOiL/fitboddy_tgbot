"""Тесты для проверки корректности наполнения БД тестовыми данными."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.equipment import Equipment

pytestmark = pytest.mark.asyncio


class TestDatabaseSeeding:
    """Тесты для проверки наполнения БД."""

    async def test_equipment_seeded(
        self, db_session: AsyncSession, sample_equipment: list[Equipment]
    ) -> None:
        """Проверяет, что оборудование корректно создано в БД."""
        result = await db_session.execute(select(Equipment))
        equipment_list: list[Equipment] = list(result.scalars().all())

        assert len(equipment_list) == 4
        equipment_names: set[str] = {e.name for e in equipment_list}
        assert "dumbbells" in equipment_names
        assert "barbell" in equipment_names
        assert "none" in equipment_names
        assert "resistance_bands" in equipment_names
