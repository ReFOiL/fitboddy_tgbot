from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Any, Awaitable, Callable, Dict

from src.application.services.metrics import bot_messages_total


class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lstrip("/")
            bot_messages_total.labels(command=command).inc()
        return await handler(event, data)

