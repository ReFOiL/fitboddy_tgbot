"""Тренировка на сегодня: меню и команда /today."""
from __future__ import annotations

import structlog
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines, workout_title
from src.application.services.user_plan_service import UserPlanService
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_TODAY_WORKOUT
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


def _scaled_int(value: int | None, mult: float) -> int | None:
    if value is None:
        return None
    return max(1, int(round(value * mult)))


@router.message(Command("today"))
@router.message(F.text == MENU_TODAY_WORKOUT)
@inject
async def cmd_today(
    message: Message,
    user_plan_service: UserPlanService = Provide[Container.user_plan_service],
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    async with uow:
        user = await uow.users.get_by_telegram_id(telegram_id)
    if not user:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
        return
    plan = await user_plan_service.get_or_create_plan(user.id)
    if not plan:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    today = date.today()
    async with uow:
        scheduled = await uow.scheduled_workouts.get_by_plan_and_date(plan.id, today)
    rows = ordered_lines(scheduled) if scheduled else []
    if not scheduled or not rows:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    mult = float(scheduled.volume_multiplier or 1.0)
    lines = [BotTexts.TODAY_HEADER, "", workout_title(scheduled), f"Объём: ×{mult:.1f}", ""]
    ordered = rows
    for i, we in enumerate(ordered, start=1):
        name = we.exercise.name if we.exercise else "—"
        sets = _scaled_int(we.sets, mult)
        reps = _scaled_int(we.reps, mult)
        part = ""
        if sets and reps:
            part = f"{sets}×{reps}"
        elif we.duration_seconds:
            dur = _scaled_int(we.duration_seconds, mult) or we.duration_seconds
            part = f"{dur} сек"
        lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))
    lines.append("")
    inline_buttons = [
        [
            InlineKeyboardButton(
                text=f"{i}. {we.exercise.name if we.exercise else '—'}",
                callback_data=f"exercise:{scheduled.id}:{i}",
            )
        ]
        for i, we in enumerate(ordered, start=1)
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    logger.info(
        "bot.workout.viewed_today",
        user_id=user.id,
        telegram_id=telegram_id,
        scheduled_workout_id=scheduled.id,
        exercise_count=len(ordered),
    )
    await message.answer("\n".join(lines), reply_markup=reply_markup)
