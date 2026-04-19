"""Контроллер админки: CRUD шаблонов тренировок."""
from __future__ import annotations

import structlog

from src.application.services.workout_template_admin import WorkoutTemplateAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.workout_schemas import (
    MessageOut,
    WorkoutExercisesOrderUpdate,
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
        # Заполняем связи для каждого шаблона
        result = []
        for t in templates:
            out = WorkoutTemplateOut.model_validate(t)
            # Заполняем required_equipment из связей
            if hasattr(t, 'required_equipment') and t.required_equipment:
                from src.presentation.web_admin.equipment_schemas import EquipmentOut
                out.required_equipment = [EquipmentOut.model_validate(eq) for eq in t.required_equipment]
            result.append(out)
        return self.ok(result)

    async def get(self, template_id: int) -> ControllerResult[WorkoutTemplateOut]:
        template = await self._service.get_by_id(template_id)
        if template is None:
            return self.not_found("Workout template not found")
        out = WorkoutTemplateOut.model_validate(template)
        # Заполняем связи
        if hasattr(template, 'required_equipment') and template.required_equipment:
            from src.presentation.web_admin.equipment_schemas import EquipmentOut
            out.required_equipment = [EquipmentOut.model_validate(eq) for eq in template.required_equipment]
        return self.ok(out)

    async def create(self, data: WorkoutTemplateCreate) -> ControllerResult[WorkoutTemplateOut]:
        exercises = [e.model_dump() for e in data.exercises] if data.exercises else None
        template = await self._service.create(
            title=data.title,
            goal=data.goal,
            difficulty=data.difficulty,
            days_per_week=data.days_per_week,
            description=data.description,
            is_active=data.is_active,
            user_id=data.user_id,
            exercises=exercises,
            required_equipment_ids=data.required_equipment_ids,
            intensity_factor=data.intensity_factor,
            workout_category=data.workout_category.value if hasattr(data.workout_category, 'value') else data.workout_category,
            min_age=data.min_age,
            max_age=data.max_age,
        )
        logger.info(
            "admin.workout_template.created",
            template_id=template.id,
            title=template.title,
            goal=template.goal,
            exercise_count=len(template.workout_exercises),
        )
        out = WorkoutTemplateOut.model_validate(template)
        # Заполняем связи
        if hasattr(template, 'required_equipment') and template.required_equipment:
            from src.presentation.web_admin.equipment_schemas import EquipmentOut
            out.required_equipment = [EquipmentOut.model_validate(eq) for eq in template.required_equipment]
        return self.ok(out)

    async def update(
        self, template_id: int, data: WorkoutTemplateUpdate
    ) -> ControllerResult[WorkoutTemplateOut]:
        updates = data.model_dump(exclude_unset=True, mode="python")
        exercises = updates.pop("exercises", None)
        required_equipment_ids = updates.pop("required_equipment_ids", None)
        
        # Обработка workout_category enum
        if "workout_category" in updates and updates["workout_category"] is not None:
            if hasattr(updates["workout_category"], 'value'):
                updates["workout_category"] = updates["workout_category"].value
        
        template = await self._service.update(
            template_id,
            exercises=exercises,
            required_equipment_ids=required_equipment_ids,
            **updates
        )
        if template is None:
            logger.warning("admin.workout_template.update_not_found", template_id=template_id)
            return self.not_found("Workout template not found")
        logger.info(
            "admin.workout_template.updated",
            template_id=template.id,
            title=template.title,
            updated_fields=list(updates.keys()) + (["exercises"] if exercises is not None else []),
        )
        out = WorkoutTemplateOut.model_validate(template)
        # Заполняем связи
        if hasattr(template, 'required_equipment') and template.required_equipment:
            from src.presentation.web_admin.equipment_schemas import EquipmentOut
            out.required_equipment = [EquipmentOut.model_validate(eq) for eq in template.required_equipment]
        return self.ok(out)

    async def update_exercises_order(
        self, template_id: int, data: WorkoutExercisesOrderUpdate
    ) -> ControllerResult[WorkoutTemplateOut]:
        template = await self._service.update_exercises_order(
            template_id, data.exercise_ids
        )
        if template is None:
            logger.warning(
                "admin.workout_template.update_order_not_found_or_invalid",
                template_id=template_id,
            )
            return self.not_found(
                "Workout template not found or exercise_ids do not match template"
            )
        logger.info(
            "admin.workout_template.exercises_order_updated",
            template_id=template.id,
            exercise_count=len(data.exercise_ids),
        )
        return self.ok(WorkoutTemplateOut.model_validate(template))

    async def delete(self, template_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(template_id)
        if not ok:
            logger.warning("admin.workout_template.delete_not_found", template_id=template_id)
            return self.not_found("Workout template not found")
        logger.info("admin.workout_template.deleted", template_id=template_id)
        return self.ok(MessageOut(message="Workout template deleted"))
