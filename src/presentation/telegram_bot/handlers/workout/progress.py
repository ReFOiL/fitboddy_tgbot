"""Отметка «выполнено» для тренировки на сегодня (кнопка меню)."""
from __future__ import annotations

import structlog
from datetime import date

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_MARK_DONE
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


@router.message(F.text == MENU_MARK_DONE)
@inject
async def cmd_done(
    message: Message,
    user_plan_service: UserPlanService = Provide[Container.user_plan_service],
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
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
        if not scheduled:
            await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
            return
        if scheduled.is_completed:
            await message.answer(BotTexts.DONE_ALREADY, reply_markup=main_menu())
            return
        await uow.scheduled_workouts.mark_completed(scheduled.id)
        await uow.commit()
        logger.info(
            "bot.workout.completed",
            user_id=user.id,
            telegram_id=telegram_id,
            scheduled_workout_id=scheduled.id,
            scheduled_for=scheduled.scheduled_for.isoformat(),
        )
    effort_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Легко", callback_data=f"effort:easy:{scheduled.id}"),
                InlineKeyboardButton(text="Нормально", callback_data=f"effort:ok:{scheduled.id}"),
                InlineKeyboardButton(text="Тяжело", callback_data=f"effort:hard:{scheduled.id}"),
            ]
        ]
    )
    await message.answer(BotTexts.DONE_OK + "\n\n" + BotTexts.EFFORT_PROMPT, reply_markup=effort_kb)
