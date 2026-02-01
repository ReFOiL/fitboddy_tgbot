from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.presentation.telegram_bot.flows.workouts import WorkoutsFlow
from src.presentation.telegram_bot.keyboards.builders import MENU_WORKOUTS
from src.shared.di.containers import Container


router = Router()


@router.message(F.text == MENU_WORKOUTS)
@inject
async def workouts_handler(
    message: Message,
    state: FSMContext,
    flow: WorkoutsFlow = Provide[Container.workouts_flow],
) -> None:
    await flow.start(message, state)
