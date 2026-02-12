"""Команда /today — тренировка на сегодня."""
from __future__ import annotations

import structlog

from datetime import date

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_TODAY_WORKOUT
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


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
    plan = await user_plan_service.create_or_get_active_plan(user.id)
    if not plan:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    today = date.today()
    async with uow:
        scheduled = await uow.scheduled_workouts.get_by_plan_and_date(plan.id, today)
    if not scheduled or not scheduled.template:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    lines = [BotTexts.TODAY_HEADER, "", scheduled.template.title, ""]
    for i, we in enumerate(
        sorted(scheduled.template.workout_exercises, key=lambda x: x.sort_order),
        start=1,
    ):
        name = we.exercise.name if we.exercise else "—"
        part = f"{we.sets}×{we.reps}" if we.sets and we.reps else ""
        if we.duration_seconds:
            part = f"{we.duration_seconds} сек" if not part else f"{part}, {we.duration_seconds} сек"
        lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))
    lines.append("")
    # Inline-кнопки по одному на упражнение
    ordered = sorted(
        scheduled.template.workout_exercises,
        key=lambda x: x.sort_order,
    )
    inline_buttons = [
        [InlineKeyboardButton(
            text=f"{i}. {we.exercise.name if we.exercise else '—'}",
            callback_data=f"exercise:{i}",
        )]
        for i, we in enumerate(ordered, start=1)
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    logger.info(
        "bot.workout.viewed_today",
        user_id=user.id,
        telegram_id=telegram_id,
        scheduled_workout_id=scheduled.id,
        template_id=scheduled.template_id,
        exercise_count=len(ordered),
    )
    await message.answer("\n".join(lines), reply_markup=reply_markup)
