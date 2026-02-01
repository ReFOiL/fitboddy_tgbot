from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.application.services.user_registration import UserRegistrationService
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container


router = Router()


@router.message(CommandStart())
@router.message(F.text == "Старт")
@inject
async def start_handler(
    message: Message,
    user_service: UserRegistrationService = Provide[Container.user_registration_service],
) -> None:
    if message.from_user is None:
        return
    await user_service.ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(BotTexts.START_WELCOME, reply_markup=main_menu())

