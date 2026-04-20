"""Показ упражнения с видео — callback exercise:{scheduled_id}:{index}."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.query import (
    GetExerciseDetailUseCase,
    WorkoutQueryAccessDenied,
    WorkoutQueryExerciseNotFound,
    WorkoutQueryUserNotFound,
)
from src.application.use_cases.workout.callback import (
    CallbackExerciseReplacementNotAvailableError,
    CallbackUserNotFoundError,
    CallbackWorkoutAccessDeniedError,
    CallbackWorkoutAlreadyCompletedError,
    CallbackWorkoutNotFoundError,
    ReplaceWorkoutExerciseRequest,
    ReplaceWorkoutExerciseUseCase,
)
from src.infrastructure.external.file_storage import VideoFileStorage
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.presenters.workout import WorkoutLoadFormatter
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


class ExerciseCallbackPayloadParser:
    @staticmethod
    def parse(raw_data: str | None, prefix: str = "exercise") -> tuple[int, int] | None:
        if raw_data is None:
            return None
        parts = raw_data.split(":")
        if len(parts) != 3 or parts[0] != prefix:
            return None
        try:
            _, scheduled_id_str, index_str = parts
            scheduled_id = int(scheduled_id_str)
            index = int(index_str)
        except (ValueError, IndexError):
            return None
        if index < 1:
            return None
        return scheduled_id, index


@router.callback_query(F.data.startswith("exercise:"))
@inject
async def exercise_callback(
    callback: CallbackQuery,
    use_case: GetExerciseDetailUseCase = Provide[Container.get_exercise_detail_use_case],
    video_storage: VideoFileStorage = Provide[Container.video_file_storage],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    parsed = ExerciseCallbackPayloadParser.parse(callback.data)
    if parsed is None:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    scheduled_id, index = parsed
    try:
        data = await use_case.get_detail(callback.from_user.id, scheduled_id, index)
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except CallbackWorkoutAccessDeniedError:
        await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
        return
    except CallbackWorkoutNotFoundError:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return

    mult = float(data.scheduled.volume_multiplier or 1.0)
    lines = [f"🏋️ {data.exercise.name}", ""]
    if data.exercise.description:
        lines.append(data.exercise.description)
        lines.append("")
    sets = WorkoutLoadFormatter.scale_int(data.workout_exercise.sets, mult)
    reps = WorkoutLoadFormatter.scale_int(data.workout_exercise.reps, mult)
    if sets and reps:
        lines.append(f"Подходы: {sets} × {reps}")
    elif data.workout_exercise.duration_seconds:
        dur = (
            WorkoutLoadFormatter.scale_int(data.workout_exercise.duration_seconds, mult)
            or data.workout_exercise.duration_seconds
        )
        lines.append(f"Длительность: {dur} сек")
    if data.workout_exercise.rest_seconds:
        lines.append(f"Отдых: {data.workout_exercise.rest_seconds} сек")
    text = "\n".join(lines)
    video_url: str | None = None
    if data.exercise.video_url and data.exercise.video_url.startswith("videos/"):
        try:
            video_url = await video_storage.get_video_url(data.exercise.video_url)
        except (OSError, ValueError) as e:
            logger.warning(
                "bot.exercise.video_url_failed",
                user_id=data.user_id,
                exercise_id=data.exercise.id,
                video_url=data.exercise.video_url,
                error=str(e),
            )

    await callback.answer()
    logger.info(
        "bot.exercise.viewed",
        user_id=data.user_id,
        telegram_id=data.telegram_id,
        exercise_id=data.exercise.id,
        exercise_name=data.exercise.name,
        has_video=bool(video_url),
        scheduled_workout_id=data.scheduled.id,
    )
    replace_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Заменить упражнение",
                    callback_data=f"replace_exercise:{scheduled_id}:{index}",
                )
            ]
        ]
    )
    if video_url:
        await callback.message.answer_video(
            video=video_url,
            caption=text,
            reply_markup=replace_markup,
        )
    else:
        await callback.message.answer(text, reply_markup=replace_markup)


@router.callback_query(F.data.startswith("replace_exercise:"))
@inject
async def replace_exercise_callback(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    parsed = ExerciseCallbackPayloadParser.parse(callback.data, prefix="replace_exercise")
    if parsed is None:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    scheduled_id, index = parsed
    try:
        result = await ReplaceWorkoutExerciseUseCase(uow).replace(
            ReplaceWorkoutExerciseRequest(
                tg_user_id=callback.from_user.id,
                scheduled_id=scheduled_id,
                index=index,
            )
        )
    except WorkoutQueryUserNotFound:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except WorkoutQueryAccessDenied:
        await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
        return
    except WorkoutQueryExerciseNotFound:
        await callback.answer(BotTexts.EXERCISE_NO_EXERCISE, show_alert=True)
        return
    except CallbackWorkoutAlreadyCompletedError:
        await callback.answer(BotTexts.DONE_ALREADY, show_alert=True)
        return
    except CallbackExerciseReplacementNotAvailableError:
        await callback.answer(BotTexts.WORKOUT_REPLACE_UNAVAILABLE, show_alert=True)
        return
    await callback.answer("Упражнение заменено")
    logger.info(
        "bot.exercise.replaced",
        user_id=result.user_id,
        scheduled_id=result.scheduled_id,
        index=result.index,
        previous_exercise_name=result.previous_exercise_name,
        replacement_exercise_name=result.replacement_exercise_name,
    )
    await callback.message.answer(
        BotTexts.WORKOUT_REPLACED.format(
            old_name=result.previous_exercise_name,
            new_name=result.replacement_exercise_name,
        ),
        reply_markup=main_menu(),
    )
