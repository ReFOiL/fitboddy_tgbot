"""Контроллер админки: CRUD справочника оборудования."""
from __future__ import annotations

import structlog

from src.application.services.equipment_admin import EquipmentAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.equipment_schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate
from src.presentation.web_admin.workout_schemas import MessageOut

logger = structlog.get_logger()


class EquipmentController(BaseController):
    def __init__(self, service: EquipmentAdminService) -> None:
        super().__init__()
        self._service = service

    async def list_all(
        self, *, is_active: bool | None = None, category: str | None = None
    ) -> ControllerResult[list[EquipmentOut]]:
        items = await self._service.list_all(is_active=is_active, category=category)
        return self.ok([EquipmentOut.model_validate(e) for e in items])

    async def get(self, equipment_id: int) -> ControllerResult[EquipmentOut]:
        equipment = await self._service.get_by_id(equipment_id)
        if equipment is None:
            return self.not_found("Equipment not found")
        return self.ok(EquipmentOut.model_validate(equipment))

    async def create(self, data: EquipmentCreate) -> ControllerResult[EquipmentOut]:
        try:
            equipment = await self._service.create(
                name=data.name,
                display_name=data.display_name,
                category=data.category,
                is_home_friendly=data.is_home_friendly,
                is_active=data.is_active,
            )
            logger.info("admin.equipment.created", equipment_id=equipment.id, name=equipment.name)
        except ValueError as e:
            logger.warning("admin.equipment.create_failed", name=data.name, error=str(e))
            return self.bad_request(str(e))
        return self.ok(EquipmentOut.model_validate(equipment))

    async def update(
        self, equipment_id: int, data: EquipmentUpdate
    ) -> ControllerResult[EquipmentOut]:
        kwargs = data.model_dump(exclude_unset=True)
        equipment = await self._service.update(equipment_id, **kwargs)
        if equipment is None:
            return self.not_found("Equipment not found")
        logger.info(
            "admin.equipment.updated",
            equipment_id=equipment.id,
            updated_fields=list(kwargs.keys()),
        )
        return self.ok(EquipmentOut.model_validate(equipment))

    async def delete(self, equipment_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(equipment_id)
        if not ok:
            logger.warning("admin.equipment.delete_not_found", equipment_id=equipment_id)
            return self.not_found("Equipment not found")
        logger.info("admin.equipment.deleted", equipment_id=equipment_id)
        return self.ok(MessageOut(message="Equipment deleted"))
