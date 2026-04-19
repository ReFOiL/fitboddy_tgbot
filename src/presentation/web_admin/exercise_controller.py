"""Контроллер админки: CRUD упражнений."""
from __future__ import annotations

import structlog

from src.application.services.exercise_admin import ExerciseAdminService
from src.infrastructure.external.file_storage import VideoFileStorage
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.admin_schemas import (
    ExerciseCreate,
    ExerciseOut,
    ExerciseUpdate,
    MessageOut,
)

logger = structlog.get_logger()


class ExerciseController(BaseController):
    def __init__(self, service: ExerciseAdminService, video_storage: VideoFileStorage) -> None:
        super().__init__()
        self._service = service
        self._video_storage = video_storage

    async def list_all(self) -> ControllerResult[list[ExerciseOut]]:
        exercises = await self._service.list_all()
        out_list = [ExerciseOut.model_validate(e) for e in exercises]
        for out, exercise in zip(out_list, exercises):
            await self._set_stream_url(out, exercise.video_url)
        return self.ok(out_list)

    async def get(self, exercise_id: int) -> ControllerResult[ExerciseOut | None]:
        exercise = await self._service.get_by_id(exercise_id)
        if exercise is None:
            return self.not_found("Exercise not found")
        out = ExerciseOut.model_validate(exercise)
        await self._set_stream_url(out, exercise.video_url)
        return self.ok(out)

    async def create(self, data: ExerciseCreate) -> ControllerResult[ExerciseOut | None]:
        try:
            exercise = await self._service.create(
                name=data.name,
                description=data.description,
                video_url=data.video_url,
                muscle_ids=data.muscle_ids,
                equipment=data.equipment,
                is_cardio=data.is_cardio,
                difficulty=data.difficulty,
                contraindication_ids=data.contraindication_ids,
                workout_category=data.workout_category,
            )
            logger.info(
                "admin.exercise.created",
                exercise_id=exercise.id,
                name=exercise.name,
                has_video=bool(exercise.video_url),
                muscle_count=len(exercise.muscles),
            )
        except ValueError as e:
            logger.warning("admin.exercise.create_failed", name=data.name, error=str(e))
            return self.bad_request(str(e))
        out = ExerciseOut.model_validate(exercise)
        await self._set_stream_url(out, exercise.video_url)
        return self.ok(out)

    async def update(
        self, exercise_id: int, data: ExerciseUpdate
    ) -> ControllerResult[ExerciseOut | None]:
        updates = data.model_dump(exclude_unset=True, mode="python")
        exercise = await self._service.update(exercise_id, **updates)
        if exercise is None:
            logger.warning("admin.exercise.update_not_found", exercise_id=exercise_id)
            return self.not_found("Exercise not found")
        logger.info(
            "admin.exercise.updated",
            exercise_id=exercise.id,
            name=exercise.name,
            updated_fields=list(updates.keys()),
        )
        out = ExerciseOut.model_validate(exercise)
        await self._set_stream_url(out, exercise.video_url)
        return self.ok(out)

    async def _set_stream_url(self, out: ExerciseOut, video_url: str | None) -> None:
        if not video_url or not video_url.startswith("videos/"):
            return
        # Используем прокси-эндпоинт для получения видео
        # Формат: /api/v1/admin/videos/{object_key}
        # Токен будет добавлен на фронтенде через query параметр (браузер не отправляет заголовки при загрузке через <video src>)
        out.video_stream_url = f"/api/v1/admin/videos/{video_url}"

    async def delete(self, exercise_id: int) -> ControllerResult[MessageOut]:
        ok = await self._service.delete(exercise_id)
        if not ok:
            logger.warning("admin.exercise.delete_not_found", exercise_id=exercise_id)
            return self.not_found("Exercise not found")
        logger.info("admin.exercise.deleted", exercise_id=exercise_id)
        return self.ok(MessageOut(message="Exercise deleted"))
