from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.application.interfaces.repositories import UnitOfWork
from src.presentation.telegram_bot.flows import BaseFlow, NavigationMixin, ResetStateMixin, UserContextMixin
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts


class WorkoutsFlow(BaseFlow, UserContextMixin, NavigationMixin, ResetStateMixin):
    """Раздел «Тренировки»: план живёт в /myplan, без шаблонов в БД."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def start(self, message: Message, state: FSMContext) -> None:
        await self._reset_state(state)
        await self.process(message, state)

    async def process(self, message: Message, state: FSMContext) -> None:
        user_id = self._user_id(message)
        if user_id is None:
            return
        text = message.text or ""
        if self._is_exit(text):
            await message.answer(BotTexts.WORKOUTS_EXITED, reply_markup=main_menu())
            return
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(user_id)
            if user is None:
                await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
                return
            answers = await self._uow.user_answers.list_by_user_id(user.id)
            if not answers:
                await message.answer(BotTexts.WORKOUTS_COMPLETE_QUESTIONNAIRE, reply_markup=main_menu())
                return

        await message.answer(BotTexts.WORKOUTS_USE_MY_PLAN, reply_markup=main_menu())
