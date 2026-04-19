"""Колбэки: выбор тренировки из плана, завершение, оценка нагрузки."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dependency_injector.wiring import Provide, inject

from src.application.use_cases.workout.callback_use_cases import (
    CallbackUserNotFoundError,
    CallbackWorkoutAccessDeniedError,
    CallbackWorkoutAlreadyCompletedError,
    CallbackWorkoutNotFoundError,
    WorkoutCallbackUseCases,
)
from src.application.services.scheduled_workout_lines import ordered_lines, workout_title
from src.domain.entities.training_plan import ScheduledWorkout
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


class CallbackPayloadParser:
    @staticmethod
    def int_after_prefix(raw: str | None, prefix: str) -> int | None:
        if not raw or not raw.startswith(prefix):
            return None
        try:
            return int(raw.split(":", 1)[1])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def effort(raw: str | None) -> tuple[str, int] | None:
        if not raw:
            return None
        parts = raw.split(":")
        if len(parts) != 3 or parts[0] != "effort":
            return None
        level = parts[1]
        if level not in ("easy", "ok", "hard"):
            return None
        try:
            sid = int(parts[2])
        except ValueError:
            return None
        return level, sid


class WorkoutMessageFormatter:
    @staticmethod
    def _scaled_int(value: int | None, mult: float) -> int | None:
        if value is None:
            return None
        return max(1, int(round(value * mult)))

    @classmethod
    def workout_detail(cls, sw: ScheduledWorkout) -> tuple[str, InlineKeyboardMarkup]:
        title = workout_title(sw)
        mult = float(sw.volume_multiplier or 1.0)
        lines = [BotTexts.WORKOUT_DETAIL_HEADER, "", title, f"Объём недели: ×{mult:.1f}", ""]
        ordered = ordered_lines(sw)
        for i, we in enumerate(ordered, start=1):
            name = we.exercise.name if we.exercise else "—"
            sets = cls._scaled_int(we.sets, mult)
            reps = cls._scaled_int(we.reps, mult)
            part = ""
            if sets and reps:
                part = f"{sets}×{reps}"
            elif we.duration_seconds:
                dur = cls._scaled_int(we.duration_seconds, mult) or we.duration_seconds
                part = f"{dur} сек"
            lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))

        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text=f"{i}. {we.exercise.name if we.exercise else '—'}",
                    callback_data=f"exercise:{sw.id}:{i}",
                )
            ]
            for i, we in enumerate(ordered, start=1)
        ]
        if not sw.is_completed:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="✅ Выполнено",
                        callback_data=f"complete_workout:{sw.id}",
                    )
                ]
            )
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("workout:"))
@inject
async def cb_workout_detail(
    callback: CallbackQuery,
    use_cases: WorkoutCallbackUseCases = Provide[Container.workout_callback_use_cases],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    sid = CallbackPayloadParser.int_after_prefix(callback.data, "workout:")
    if sid is None:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    try:
        detail = await use_cases.get_detail(callback.from_user.id, sid)
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except CallbackWorkoutNotFoundError:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    text, markup = WorkoutMessageFormatter.workout_detail(detail.scheduled_workout)

    await callback.answer()
    logger.info("bot.workout.plan_detail", user_id=detail.user_id, scheduled_id=sid)
    await callback.message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("complete_workout:"))
@inject
async def cb_complete_workout(
    callback: CallbackQuery,
    use_cases: WorkoutCallbackUseCases = Provide[Container.workout_callback_use_cases],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    sid = CallbackPayloadParser.int_after_prefix(callback.data, "complete_workout:")
    if sid is None:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    try:
        user_id = await use_cases.complete_workout(callback.from_user.id, sid)
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except CallbackWorkoutNotFoundError:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return
    except CallbackWorkoutAlreadyCompletedError:
        await callback.answer(BotTexts.DONE_ALREADY, show_alert=True)
        return

    logger.info("bot.workout.completed_callback", user_id=user_id, scheduled_id=sid)

    effort_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Легко", callback_data=f"effort:easy:{sid}"),
                InlineKeyboardButton(text="Нормально", callback_data=f"effort:ok:{sid}"),
                InlineKeyboardButton(text="Тяжело", callback_data=f"effort:hard:{sid}"),
            ]
        ]
    )
    await callback.answer()
    await callback.message.answer(BotTexts.DONE_OK + "\n\n" + BotTexts.EFFORT_PROMPT, reply_markup=effort_kb)


@router.callback_query(F.data.startswith("effort:"))
@inject
async def cb_effort(
    callback: CallbackQuery,
    use_cases: WorkoutCallbackUseCases = Provide[Container.workout_callback_use_cases],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    parsed = CallbackPayloadParser.effort(callback.data)
    if parsed is None:
        await callback.answer()
        return
    level, sid = parsed

    try:
        user_id = await use_cases.save_effort(callback.from_user.id, sid, level)
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except (CallbackWorkoutNotFoundError, CallbackWorkoutAccessDeniedError):
        await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
        return

    logger.info("bot.workout.effort", user_id=user_id, scheduled_id=sid, level=level)

    await callback.answer()
    await callback.message.answer(BotTexts.EFFORT_SAVED, reply_markup=main_menu())
