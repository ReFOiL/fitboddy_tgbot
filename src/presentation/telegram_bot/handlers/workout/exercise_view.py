"""Показ упражнения с видео — callback exercise:{scheduled_id}:{index}."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines
from src.infrastructure.external.file_storage import VideoFileStorage
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


def _scaled_int(value: int | None, mult: float) -> int | None:
    if value is None:
        return None
    return max(1, int(round(value * mult)))


@router.callback_query(F.data.startswith("exercise:"))
@inject
async def exercise_callback(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
    video_storage: VideoFileStorage = Provide[Container.video_file_storage],
) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    if not telegram_id or not callback.message:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    try:
        _, sid_s, idx_s = parts
        scheduled_id = int(sid_s)
        index = int(idx_s)
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

        scheduled = await uow.scheduled_workouts.get_by_id(scheduled_id)
        if scheduled is None or scheduled.plan is None or scheduled.plan.user_id != user.id:
            await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
            return

        ordered = ordered_lines(scheduled)
        if not ordered:
            await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
            return
        if index > len(ordered):
            await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
            return
        we = ordered[index - 1]
        exercise = we.exercise
        if not exercise:
            await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
            return

        mult = float(scheduled.volume_multiplier or 1.0)
        lines = [f"🏋️ {exercise.name}", ""]
        if exercise.description:
            lines.append(exercise.description)
            lines.append("")
        sets = _scaled_int(we.sets, mult)
        reps = _scaled_int(we.reps, mult)
        if sets and reps:
            lines.append(f"Подходы: {sets} × {reps}")
        elif we.duration_seconds:
            dur = _scaled_int(we.duration_seconds, mult) or we.duration_seconds
            lines.append(f"Длительность: {dur} сек")
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
        await callback.message.answer_video(
            video=video_url,
            caption=text,
            reply_markup=main_menu(),
        )
    else:
        await callback.message.answer(text, reply_markup=main_menu())
