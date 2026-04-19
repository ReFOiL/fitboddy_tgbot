"""Админ-сервис: CRUD справочника оборудования."""
from __future__ import annotations

import structlog
from typing import TypedDict

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.equipment import Equipment


class EquipmentUpdates(TypedDict, total=False):
    display_name: str
    category: str
    is_home_friendly: bool
    is_active: bool

logger = structlog.get_logger()


class EquipmentAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_all(self, *, is_active: bool | None = None, category: str | None = None) -> list[Equipment]:
        async with self._uow:
            all_items = await self._uow.equipment.list_all()
            if is_active is not None:
                all_items = [e for e in all_items if e.is_active == is_active]
            if category:
                all_items = [e for e in all_items if e.category == category]
            return all_items

    async def get_by_id(self, equipment_id: int) -> Equipment | None:
        async with self._uow:
            return await self._uow.equipment.get_by_id(equipment_id)

    async def create(
        self,
        *,
        name: str,
        display_name: str,
        category: str,
        is_home_friendly: bool = False,
        is_active: bool = True,
    ) -> Equipment:
        async with self._uow:
            existing = await self._uow.equipment.get_by_name(name)
            if existing is not None:
                raise ValueError(f"Equipment with name '{name}' already exists")
            equipment = Equipment(
                name=name,
                display_name=display_name,
                category=category,
                is_home_friendly=is_home_friendly,
                is_active=is_active,
            )
            await self._uow.equipment.add(equipment)
            await self._uow.flush()
            await self._uow.commit()
            logger.info("admin.equipment.created", equipment_id=equipment.id, name=equipment.name)
        return equipment

    async def update(self, equipment_id: int, **kwargs: str | bool) -> Equipment | None:
        async with self._uow:
            equipment = await self._uow.equipment.get_by_id(equipment_id)
            if equipment is None:
                return None
            if "display_name" in kwargs and kwargs["display_name"] is not None:
                equipment.display_name = kwargs["display_name"]
            if "category" in kwargs and kwargs["category"] is not None:
                equipment.category = kwargs["category"]
            if "is_home_friendly" in kwargs and kwargs["is_home_friendly"] is not None:
                equipment.is_home_friendly = kwargs["is_home_friendly"]
            if "is_active" in kwargs and kwargs["is_active"] is not None:
                equipment.is_active = kwargs["is_active"]
            await self._uow.commit()
            logger.info("admin.equipment.updated", equipment_id=equipment.id, updated_fields=list(kwargs.keys()))
        return equipment

    async def delete(self, equipment_id: int) -> bool:
        """Мягкое удаление: устанавливает is_active = False."""
        async with self._uow:
            equipment = await self._uow.equipment.get_by_id(equipment_id)
            if equipment is None:
                return False
            equipment.is_active = False
            await self._uow.commit()
            logger.info("admin.equipment.deleted", equipment_id=equipment_id)
        return True
