from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.metrics import user_registrations_total
from src.domain.entities.user import User


class UserRegistrationService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def ensure_user(self, telegram_id: int, username: str | None) -> User:
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(telegram_id)
            if user is None:
                user = User(telegram_id=telegram_id, username=username)
                await self._uow.users.add(user)
                await self._uow.commit()
                user_registrations_total.inc()
            return user
