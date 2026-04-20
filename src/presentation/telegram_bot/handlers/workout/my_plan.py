"""Мой план: меню и команда /myplan."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.application.use_cases.workout.query import (
    GetMyPlanUseCase,
    WorkoutQueryPlanNotFound,
    WorkoutQueryUserNotFound,
)
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_MY_PLAN
from src.presentation.telegram_bot.presenters.workout import WorkoutPlanListFormatter
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

router = Router()


@router.message(Command("myplan"))
@router.message(F.text == MENU_MY_PLAN)
@inject
async def cmd_myplan(
    message: Message,
    use_case: GetMyPlanUseCase = Provide[Container.get_my_plan_use_case],
) -> None:
    if not message.from_user:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    try:
        data = await use_case.get_plan(message.from_user.id)
    except WorkoutQueryUserNotFound:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
        return
    except WorkoutQueryPlanNotFound:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    text, markup = WorkoutPlanListFormatter().format_plan(data.plan)
    await message.answer(text, reply_markup=markup or main_menu())
