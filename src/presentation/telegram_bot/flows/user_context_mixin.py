from __future__ import annotations

from aiogram.types import Message


class UserContextMixin:
    @staticmethod
    def _user_id(message: Message) -> int | None:
        if message.from_user is None:
            return None
        return message.from_user.id
