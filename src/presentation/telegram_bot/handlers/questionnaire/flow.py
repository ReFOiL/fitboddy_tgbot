from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.presentation.telegram_bot.flows.questionnaire import QuestionnaireFlow
from src.presentation.telegram_bot.keyboards.builders import MENU_QUESTIONNAIRE
from src.presentation.telegram_bot.states.questionnaire import QuestionnaireStates
from src.shared.di.containers import Container

router = Router()


@router.message(F.text == MENU_QUESTIONNAIRE)
@inject
async def start_questionnaire(
    message: Message,
    state: FSMContext,
    flow: QuestionnaireFlow = Provide[Container.questionnaire_flow],
) -> None:
    await state.set_state(QuestionnaireStates.in_progress)
    await flow.start(message, state)


@router.message(QuestionnaireStates.in_progress)
@inject
async def process_questionnaire(
    message: Message,
    state: FSMContext,
    flow: QuestionnaireFlow = Provide[Container.questionnaire_flow],
) -> None:
    await flow.process(message, state)




