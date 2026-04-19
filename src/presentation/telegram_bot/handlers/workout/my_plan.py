"""Мой план: меню и команда /myplan."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import workout_title
from src.application.services.user_plan_service import UserPlanService
from src.domain.entities.training_plan import TrainingPlan
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_MY_PLAN
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

router = Router()


def _format_plan(plan: TrainingPlan) -> tuple[str, InlineKeyboardMarkup | None]:
    lines = [BotTexts.PLAN_HEADER, ""]
    rows: list[list[InlineKeyboardButton]] = []
    for sw in sorted(plan.scheduled_workouts, key=lambda x: x.scheduled_for):
        title = workout_title(sw)
        done = " ✅" if sw.is_completed else ""
        lines.append(f"{sw.scheduled_for:%d.%m} — {title}{done}")
        label = f"{sw.scheduled_for:%d.%m} {title}"[:60]
        rows.append([InlineKeyboardButton(text=label, callback_data=f"workout:{sw.id}")])
    markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
    return "\n".join(lines), markup


@router.message(Command("myplan"))
@router.message(F.text == MENU_MY_PLAN)
@inject
async def cmd_myplan(
    message: Message,
    user_plan_service: UserPlanService = Provide[Container.user_plan_service],
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
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
    text, markup = _format_plan(plan)
    await message.answer(text, reply_markup=markup or main_menu())
