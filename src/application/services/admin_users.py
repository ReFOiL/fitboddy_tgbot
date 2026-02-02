from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.user import User
from src.domain.entities.user_answer import UserAnswer


class AdminUserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_users(self) -> list[User]:
        async with self._uow:
            return await self._uow.users.list_all()

    async def get_user(self, user_id: int) -> User | None:
        async with self._uow:
            return await self._uow.users.get_by_id(user_id)

    async def list_user_answers(self, user_id: int) -> list[UserAnswer]:
        async with self._uow:
            return await self._uow.user_answers.list_by_user_id(user_id)

