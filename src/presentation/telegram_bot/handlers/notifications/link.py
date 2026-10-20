from __future__ import annotations

from typing import assert_never

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.application.services.telegram_link import TelegramLinkResult, TelegramLinkService
from src.application.services.user_registration import UserRegistrationService
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container


router = Router(name="telegram_link")


def telegram_link_reply(result: TelegramLinkResult) -> str:
    match result:
        case TelegramLinkResult.LINKED:
            return BotTexts.TELEGRAM_LINK_OK
        case TelegramLinkResult.INVALID_OR_EXPIRED:
            return BotTexts.TELEGRAM_LINK_INVALID
        case TelegramLinkResult.UNAVAILABLE | TelegramLinkResult.NOT_CONFIGURED:
            return BotTexts.TELEGRAM_LINK_UNAVAILABLE
        case TelegramLinkResult.PRIVATE_ONLY:
            return BotTexts.TELEGRAM_LINK_PRIVATE
        case _ as unexpected:
            assert_never(unexpected)


@router.message(CommandStart(deep_link=True))
@inject
async def start_with_link_code(
    message: Message,
    command: CommandObject,
    user_service: UserRegistrationService = Provide[Container.user_registration_service],
    link_service: TelegramLinkService = Provide[Container.telegram_link_service],
) -> None:
    # Диплинк https://t.me/<bot>?start=<код> приходит как /start <код>.
    await _remember_local_user(message, user_service)
    result = await link_service.confirm(code=command.args or "", chat_id=message.chat.id)
    await message.answer(telegram_link_reply(result))
    await message.answer(BotTexts.START_WELCOME, reply_markup=main_menu())


@router.message(Command("link"))
@inject
async def link_command(
    message: Message,
    command: CommandObject,
    user_service: UserRegistrationService = Provide[Container.user_registration_service],
    link_service: TelegramLinkService = Provide[Container.telegram_link_service],
) -> None:
    await _remember_local_user(message, user_service)
    raw = command.args
    if raw is None or not raw.strip():
        await message.answer(BotTexts.TELEGRAM_LINK_USAGE)
        return
    result = await link_service.confirm(code=raw, chat_id=message.chat.id)
    await message.answer(telegram_link_reply(result))


async def _remember_local_user(message: Message, user_service: UserRegistrationService) -> None:
    # Локальный users.telegram_id нужен оплате и тренировкам этого бота.
    # chat_id уведомлений хранит plan-service, не эта таблица.
    if message.from_user is None:
        return
    await user_service.ensure_user(message.from_user.id, message.from_user.username)
