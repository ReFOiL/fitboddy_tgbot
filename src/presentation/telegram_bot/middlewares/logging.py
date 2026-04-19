from collections.abc import Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object],
    ) -> object:
        user = getattr(event, "from_user", None)
        logger.info("telegram_event", user_id=getattr(user, "id", None))
        return await handler(event, data)

