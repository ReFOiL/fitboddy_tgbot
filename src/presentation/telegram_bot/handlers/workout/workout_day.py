"""Тренировка на сегодня: меню и команда /today."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from src.application.services.scheduled_workout_lines import workout_title
from src.application.use_cases.workout.query import (
    GetTodayWorkoutUseCase,
    WorkoutQueryPlanNotFound,
    WorkoutQueryTodayWorkoutNotFound,
    WorkoutQueryUserNotFound,
)
from src.presentation.telegram_bot.presenters.workout import WorkoutLoadFormatter
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_TODAY_WORKOUT
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()

@router.message(Command("today"))
@router.message(F.text == MENU_TODAY_WORKOUT)
@inject
async def cmd_today(
    message: Message,
    use_case: GetTodayWorkoutUseCase = Provide[Container.get_today_workout_use_case],
) -> None:
    if not message.from_user:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    try:
        data = await use_case.get_today_workout(message.from_user.id)
    except WorkoutQueryUserNotFound:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
        return
    except WorkoutQueryPlanNotFound:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    except WorkoutQueryTodayWorkoutNotFound:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    mult = float(data.scheduled.volume_multiplier or 1.0)
    lines = [BotTexts.TODAY_HEADER, "", workout_title(data.scheduled), f"Объём: ×{mult:.1f}", ""]
    ordered = data.rows
    for i, we in enumerate(ordered, start=1):
        name = we.exercise.name if we.exercise else "—"
        part = WorkoutLoadFormatter.format_volume_part(
            sets=we.sets,
            reps=we.reps,
            duration_seconds=we.duration_seconds,
            multiplier=mult,
        )
        lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))
    lines.append("")
    inline_buttons = [
        [
            InlineKeyboardButton(
                text=f"{i}. {we.exercise.name if we.exercise else '—'}",
                callback_data=f"exercise:{data.scheduled.id}:{i}",
            )
        ]
        for i, we in enumerate(ordered, start=1)
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    logger.info(
        "bot.workout.viewed_today",
        user_id=data.user_id,
        telegram_id=data.telegram_id,
        scheduled_workout_id=data.scheduled.id,
        exercise_count=len(ordered),
    )
    await message.answer("\n".join(lines), reply_markup=reply_markup)
