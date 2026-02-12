"""Показ упражнения с видео — по нажатию inline-кнопки из «На сегодня»."""
from __future__ import annotations

import structlog

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.infrastructure.external.file_storage import VideoFileStorage
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


@router.callback_query(F.data.startswith("exercise:"))
@inject
async def exercise_callback(
    callback: CallbackQuery,
    user_plan_service: UserPlanService = Provide[Container.user_plan_service],
    uow: UnitOfWork = Provide[Container.uow],
    video_storage: VideoFileStorage = Provide[Container.video_file_storage],
) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    if not telegram_id or not callback.message:
        await callback.answer()
        return
    try:
        index = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    if index < 1:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    async with uow:
        user = await uow.users.get_by_telegram_id(telegram_id)
    if not user:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    plan = await user_plan_service.create_or_get_active_plan(user.id)
    if not plan:
        await callback.answer(BotTexts.PLAN_NO_PLAN, show_alert=True)
        return
    today = date.today()
    async with uow:
        scheduled = await uow.scheduled_workouts.get_by_plan_and_date(plan.id, today)
    if not scheduled or not scheduled.template:
        await callback.answer(BotTexts.TODAY_NO_WORKOUT, show_alert=True)
        return
    ordered = sorted(
        scheduled.template.workout_exercises,
        key=lambda x: x.sort_order,
    )
    if index > len(ordered):
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    we = ordered[index - 1]
    exercise = we.exercise
    if not exercise:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    lines = [f"🏋️ {exercise.name}", ""]
    if exercise.description:
        lines.append(exercise.description)
        lines.append("")
    if we.sets and we.reps:
        lines.append(f"Подходы: {we.sets} × {we.reps}")
    if we.duration_seconds:
        lines.append(f"Длительность: {we.duration_seconds} сек")
    if we.rest_seconds:
        lines.append(f"Отдых: {we.rest_seconds} сек")
    text = "\n".join(lines)
    video_url: str | None = None
    if exercise.video_url and exercise.video_url.startswith("videos/"):
        try:
            video_url = await video_storage.get_video_url(exercise.video_url)
        except (OSError, ValueError) as e:
            logger.warning(
                "bot.exercise.video_url_failed",
                user_id=user.id,
                exercise_id=exercise.id,
                video_url=exercise.video_url,
                error=str(e),
            )
    await callback.answer()
    logger.info(
        "bot.exercise.viewed",
        user_id=user.id,
        telegram_id=telegram_id,
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        has_video=bool(video_url),
        scheduled_workout_id=scheduled.id,
    )
    if video_url:
        # Telegram сам скачивает видео по URL с MinIO — наш сервер не участвует в передаче
        await callback.message.answer_video(
            video=video_url,
            caption=text,
            reply_markup=main_menu(),
        )
    else:
        await callback.message.answer(text, reply_markup=main_menu())
