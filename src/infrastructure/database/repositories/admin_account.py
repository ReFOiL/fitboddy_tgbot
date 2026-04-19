from __future__ import annotations

from sqlalchemy import delete, func, select

from src.application.interfaces.repositories import IAdminAccountRepository
from src.domain.entities.admin_account import AdminAccount
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class AdminAccountRepository(SQLAlchemyRepository, IAdminAccountRepository):
    async def get_by_username(self, username: str) -> AdminAccount | None:
        result = await self._session.execute(select(AdminAccount).where(AdminAccount.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: int) -> AdminAccount | None:
        result = await self._session.execute(select(AdminAccount).where(AdminAccount.id == account_id))
        return result.scalar_one_or_none()

    async def add(self, account: AdminAccount) -> None:
        self._session.add(account)

    async def list_all(self) -> list[AdminAccount]:
        result = await self._session.execute(select(AdminAccount).order_by(AdminAccount.username))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(AdminAccount))
        return int(result.scalar_one())

    async def count_superusers(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(AdminAccount).where(AdminAccount.is_superuser.is_(True))
        )
        return int(result.scalar_one())

    async def delete(self, account_id: int) -> None:
        await self._session.execute(delete(AdminAccount).where(AdminAccount.id == account_id))
