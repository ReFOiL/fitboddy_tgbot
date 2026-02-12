"""Контроллер админки: CRUD справочника противопоказаний."""
from __future__ import annotations

import structlog

from src.application.services.contraindication_admin import ContraindicationAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.workout_schemas import (
    ContraindicationCreate,
    ContraindicationOut,
    ContraindicationUpdate,
    MessageOut,
)

logger = structlog.get_logger()


class ContraindicationController(BaseController):
    def __init__(self, service: ContraindicationAdminService) -> None:
        super().__init__()
        self._service = service

    async def list_all(self) -> ControllerResult[list[ContraindicationOut]]:
        items = await self._service.list_all()
        return self.ok([ContraindicationOut.model_validate(c) for c in items])

    async def get(self, contraindication_id: int) -> ControllerResult[ContraindicationOut]:
        contra = await self._service.get_by_id(contraindication_id)
        if contra is None:
            return self.not_found("Contraindication not found")
        return self.ok(ContraindicationOut.model_validate(contra))

    async def create(self, data: ContraindicationCreate) -> ControllerResult[ContraindicationOut]:
        try:
            contra = await self._service.create(name=data.name, sort_order=data.sort_order)
            logger.info("admin.contraindication.created", contraindication_id=contra.id, name=contra.name)
        except ValueError as e:
            logger.warning("admin.contraindication.create_failed", name=data.name, error=str(e))
            return self.bad_request(str(e))
        return self.ok(ContraindicationOut.model_validate(contra))

    async def update(
        self, contraindication_id: int, data: ContraindicationUpdate
    ) -> ControllerResult[ContraindicationOut]:
        kwargs = data.model_dump(exclude_unset=True)
        contra = await self._service.update(contraindication_id, **kwargs)
        if contra is None:
            return self.not_found("Contraindication not found")
        return self.ok(ContraindicationOut.model_validate(contra))

    async def delete(self, contraindication_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(contraindication_id)
        if not ok:
            logger.warning("admin.contraindication.delete_not_found", contraindication_id=contraindication_id)
            return self.not_found("Contraindication not found")
        logger.info("admin.contraindication.deleted", contraindication_id=contraindication_id)
        return self.ok(MessageOut(message="Contraindication deleted"))
