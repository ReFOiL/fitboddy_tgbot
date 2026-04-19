from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.application.services.metrics import bot_messages_total


class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object],
    ) -> object:
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lstrip("/")
            bot_messages_total.labels(command=command).inc()
        return await handler(event, data)

