"""Контроллер админки: CRUD шаблонов тренировок."""
from __future__ import annotations

import structlog

from src.application.services.workout_template_admin import WorkoutTemplateAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.workout_schemas import (
    MessageOut,
    WorkoutTemplateCreate,
    WorkoutTemplateOut,
    WorkoutTemplateUpdate,
)

logger = structlog.get_logger()


class WorkoutTemplateController(BaseController):
    def __init__(self, service: WorkoutTemplateAdminService) -> None:
        super().__init__()
        self._service = service

    async def list_all(self) -> ControllerResult[list[WorkoutTemplateOut]]:
        templates = await self._service.list_all()
        return self.ok([WorkoutTemplateOut.model_validate(t) for t in templates])

    async def get(self, template_id: int) -> ControllerResult[WorkoutTemplateOut]:
        template = await self._service.get_by_id(template_id)
        if template is None:
            return self.not_found("Workout template not found")
        return self.ok(WorkoutTemplateOut.model_validate(template))

    async def create(self, data: WorkoutTemplateCreate) -> ControllerResult[WorkoutTemplateOut]:
        exercises = [e.model_dump() for e in data.exercises] if data.exercises else None
        template = await self._service.create(
            title=data.title,
            goal=data.goal,
            difficulty=data.difficulty,
            equipment=data.equipment,
            days_per_week=data.days_per_week,
            description=data.description,
            is_active=data.is_active,
            user_id=data.user_id,
            exercises=exercises,
        )
        logger.info(
            "admin.workout_template.created",
            template_id=template.id,
            title=template.title,
            goal=template.goal,
            exercise_count=len(template.workout_exercises),
        )
        return self.ok(WorkoutTemplateOut.model_validate(template))

    async def update(
        self, template_id: int, data: WorkoutTemplateUpdate
    ) -> ControllerResult[WorkoutTemplateOut]:
        updates = data.model_dump(exclude_unset=True, mode="python")
        exercises = updates.pop("exercises", None)
        template = await self._service.update(template_id, exercises=exercises, **updates)
        if template is None:
            logger.warning("admin.workout_template.update_not_found", template_id=template_id)
            return self.not_found("Workout template not found")
        logger.info(
            "admin.workout_template.updated",
            template_id=template.id,
            title=template.title,
            updated_fields=list(updates.keys()) + (["exercises"] if exercises is not None else []),
        )
        return self.ok(WorkoutTemplateOut.model_validate(template))

    async def delete(self, template_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(template_id)
        if not ok:
            logger.warning("admin.workout_template.delete_not_found", template_id=template_id)
            return self.not_found("Workout template not found")
        logger.info("admin.workout_template.deleted", template_id=template_id)
        return self.ok(MessageOut(message="Workout template deleted"))
