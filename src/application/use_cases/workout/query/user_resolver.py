from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout.query.errors import WorkoutQueryUserNotFound


class WorkoutTelegramUserResolver:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def resolve_user(self, tg_user_id: int):
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(tg_user_id)
        if user is None:
            raise WorkoutQueryUserNotFound()
        return user
