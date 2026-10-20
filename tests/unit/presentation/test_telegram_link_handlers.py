"""Команды /start и /link не подменяют обычный старт и оплату."""
from __future__ import annotations

from datetime import datetime, timezone
from inspect import unwrap
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Router
from aiogram.filters import CommandObject
from aiogram.types import Chat, Message, User

from src.application.services.telegram_link import TelegramLinkResult
from src.presentation.telegram_bot.dispatcher import create_dispatcher
from src.presentation.telegram_bot.handlers.notifications.link import (
    link_command,
    start_with_link_code,
    telegram_link_reply,
)
from src.presentation.telegram_bot.handlers.start import router as start_router
from src.presentation.telegram_bot.handlers.start import start_handler
from src.presentation.telegram_bot.texts import BotTexts


def _message(text: str, *, chat_id: int = 42, chat_type: str = "private") -> Message:
    return Message(
        message_id=1,
        date=datetime.now(tz=timezone.utc),
        chat=Chat(id=chat_id, type=chat_type),
        from_user=User(id=42, is_bot=False, first_name="Ann", username="ann"),
        text=text,
    )


def _fake_message(*, chat_id: int = 42, username: str | None = "ann") -> AsyncMock:
    message = AsyncMock()
    message.from_user = SimpleNamespace(id=42, username=username)
    message.chat = SimpleNamespace(id=chat_id)
    message.answer = AsyncMock()
    return message


def _walk(router: Router) -> list[Router]:
    found = [router]
    for child in router.sub_routers:
        found.extend(_walk(child))
    return found


async def _first_handler_name(dispatcher: Router, text: str) -> str | None:
    message = _message(text)
    bot = MagicMock()
    for router in _walk(dispatcher):
        for handler in router.observers["message"].handlers:
            matched, _data = await handler.check(message, bot=bot)
            if matched:
                return str(unwrap(handler.callback).__name__)
    return None


@pytest.fixture(scope="module")
def dispatcher() -> Router:
    # Роутеры — глобальные объекты: диспетчер собирается один раз за сессию модуля.
    return create_dispatcher()


def test_reply_texts_cover_every_result() -> None:
    assert telegram_link_reply(TelegramLinkResult.LINKED) == BotTexts.TELEGRAM_LINK_OK
    assert telegram_link_reply(TelegramLinkResult.INVALID_OR_EXPIRED) == BotTexts.TELEGRAM_LINK_INVALID
    assert telegram_link_reply(TelegramLinkResult.UNAVAILABLE) == BotTexts.TELEGRAM_LINK_UNAVAILABLE
    assert telegram_link_reply(TelegramLinkResult.NOT_CONFIGURED) == BotTexts.TELEGRAM_LINK_UNAVAILABLE
    assert telegram_link_reply(TelegramLinkResult.PRIVATE_ONLY) == BotTexts.TELEGRAM_LINK_PRIVATE
    assert "Готово" in BotTexts.TELEGRAM_LINK_OK
    assert "истёк" in BotTexts.TELEGRAM_LINK_INVALID


@pytest.mark.asyncio
async def test_start_with_code_links_chat_and_still_welcomes() -> None:
    message = _fake_message()
    user_service = AsyncMock()
    link_service = AsyncMock()
    link_service.confirm.return_value = TelegramLinkResult.LINKED
    command = CommandObject(command="start", args="abcd2345")
    await unwrap(start_with_link_code)(
        message,
        command,
        user_service=user_service,
        link_service=link_service,
    )
    user_service.ensure_user.assert_awaited_once_with(42, "ann")
    link_service.confirm.assert_awaited_once_with(code="abcd2345", chat_id=42)
    assert message.answer.await_args_list[0].args[0] == BotTexts.TELEGRAM_LINK_OK
    assert message.answer.await_args_list[1].args[0] == BotTexts.START_WELCOME


@pytest.mark.asyncio
async def test_link_command_without_code_does_not_call_plan_service() -> None:
    message = _fake_message()
    link_service = AsyncMock()
    await unwrap(link_command)(
        message,
        CommandObject(command="link", args=None),
        user_service=AsyncMock(),
        link_service=link_service,
    )
    link_service.confirm.assert_not_awaited()
    message.answer.assert_awaited_once_with(BotTexts.TELEGRAM_LINK_USAGE)


@pytest.mark.asyncio
async def test_link_command_reports_invalid_code() -> None:
    message = _fake_message(chat_id=-5)
    link_service = AsyncMock()
    link_service.confirm.return_value = TelegramLinkResult.PRIVATE_ONLY
    await unwrap(link_command)(
        message,
        CommandObject(command="link", args="ABCD2345"),
        user_service=AsyncMock(),
        link_service=link_service,
    )
    message.answer.assert_awaited_once_with(BotTexts.TELEGRAM_LINK_PRIVATE)


@pytest.mark.asyncio
async def test_plain_start_still_registers_user_and_shows_menu() -> None:
    message = _fake_message(username="bob")
    user_service = AsyncMock()
    await unwrap(start_handler)(message, user_service=user_service)
    user_service.ensure_user.assert_awaited_once_with(42, "bob")
    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0] == BotTexts.START_WELCOME
    assert message.answer.await_args.kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_routing_keeps_plain_start_and_sends_code_to_link_handler(dispatcher: Router) -> None:
    assert await _first_handler_name(dispatcher, "/start") == "start_handler"
    assert await _first_handler_name(dispatcher, "Старт") == "start_handler"
    assert await _first_handler_name(dispatcher, "/start ABCD2345") == "start_with_link_code"
    assert await _first_handler_name(dispatcher, "/link ABCD2345") == "link_command"


@pytest.mark.asyncio
async def test_routing_does_not_treat_start_code_as_plain_start() -> None:
    message = _message("/start ABCD2345")
    bot = MagicMock()
    matched: list[str] = []
    for handler in start_router.message.handlers:
        ok, _data = await handler.check(message, bot=bot)
        if ok:
            matched.append(unwrap(handler.callback).__name__)
    assert matched == []
