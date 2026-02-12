"""Команда /myplan — показать план на месяц."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.domain.entities.training_plan import TrainingPlan
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_MY_PLAN
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

router = Router()


def _format_plan(plan: TrainingPlan) -> str:
    lines = [BotTexts.PLAN_HEADER, ""]
    for sw in sorted(plan.scheduled_workouts, key=lambda x: x.scheduled_for):
        title = sw.template.title if sw.template else "—"
        done = " ✅" if sw.is_completed else ""
        lines.append(f"{sw.scheduled_for:%d.%m} — {title}{done}")
    return "\n".join(lines)


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
    plan = await user_plan_service.create_or_get_active_plan(user.id)
    if not plan:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    await message.answer(_format_plan(plan), reply_markup=main_menu())
