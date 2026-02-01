from __future__ import annotations

from datetime import datetime

from src.application.interfaces.repositories import UnitOfWork


class ProfileCompletionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def mark_completed(self, user_id: int) -> None:
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            if user is None:
                return
            user.has_completed_profile = True
            user.profile_completed_at = datetime.utcnow()
            await self._uow.commit()
