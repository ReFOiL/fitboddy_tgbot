import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Any, Callable, Dict, Awaitable


logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        logger.info("telegram_event", user_id=getattr(user, "id", None))
        return await handler(event, data)

