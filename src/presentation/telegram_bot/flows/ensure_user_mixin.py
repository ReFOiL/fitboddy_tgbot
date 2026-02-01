from __future__ import annotations

from aiogram.types import Message

from src.application.services.user_registration import UserRegistrationService
from src.domain.entities.user import User


class EnsureUserMixin:
    async def _ensure_user(self, message: Message, service: UserRegistrationService) -> User | None:
        if message.from_user is None:
            return None
        return await service.ensure_user(message.from_user.id, message.from_user.username)
