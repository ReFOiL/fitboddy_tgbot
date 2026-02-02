from sqlalchemy import select, desc

from src.application.interfaces.repositories import IUserRepository
from src.domain.entities.user import User
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository, IUserRepository):
    async def get_by_telegram_id(self, tg_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.telegram_id == tg_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> None:
        self._session.add(user)

    async def list_all(self) -> list[User]:
        result = await self._session.execute(select(User).order_by(desc(User.created_at)))
        return list(result.scalars().all())

