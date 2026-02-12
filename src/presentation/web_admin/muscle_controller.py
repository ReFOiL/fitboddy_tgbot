"""Контроллер админки: CRUD справочника мышечных групп."""
from __future__ import annotations

import structlog

from src.application.services.muscle_admin import MuscleAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.workout_schemas import MessageOut, MuscleCreate, MuscleOut, MuscleUpdate

logger = structlog.get_logger()


class MuscleController(BaseController):
    def __init__(self, service: MuscleAdminService) -> None:
        super().__init__()
        self._service = service

    async def list_all(self) -> ControllerResult[list[MuscleOut]]:
        items = await self._service.list_all()
        return self.ok([MuscleOut.model_validate(m) for m in items])

    async def get(self, muscle_id: int) -> ControllerResult[MuscleOut]:
        muscle = await self._service.get_by_id(muscle_id)
        if muscle is None:
            return self.not_found("Muscle not found")
        return self.ok(MuscleOut.model_validate(muscle))

    async def create(self, data: MuscleCreate) -> ControllerResult[MuscleOut]:
        try:
            muscle = await self._service.create(name=data.name, sort_order=data.sort_order)
            logger.info("admin.muscle.created", muscle_id=muscle.id, name=muscle.name)
        except ValueError as e:
            logger.warning("admin.muscle.create_failed", name=data.name, error=str(e))
            return self.bad_request(str(e))
        return self.ok(MuscleOut.model_validate(muscle))

    async def update(self, muscle_id: int, data: MuscleUpdate) -> ControllerResult[MuscleOut]:
        kwargs = data.model_dump(exclude_unset=True)
        muscle = await self._service.update(muscle_id, **kwargs)
        if muscle is None:
            return self.not_found("Muscle not found")
        return self.ok(MuscleOut.model_validate(muscle))

    async def delete(self, muscle_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(muscle_id)
        if not ok:
            logger.warning("admin.muscle.delete_not_found", muscle_id=muscle_id)
            return self.not_found("Muscle not found")
        logger.info("admin.muscle.deleted", muscle_id=muscle_id)
        return self.ok(MessageOut(message="Muscle deleted"))
