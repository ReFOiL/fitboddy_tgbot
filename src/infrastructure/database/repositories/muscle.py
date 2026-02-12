from sqlalchemy import delete, select

from src.application.interfaces.repositories import IMuscleRepository
from src.domain.entities.muscle import Muscle
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class MuscleRepository(SQLAlchemyRepository, IMuscleRepository):
    async def list_all(self) -> list[Muscle]:
        result = await self._session.execute(select(Muscle).order_by(Muscle.sort_order, Muscle.name))
        return list(result.scalars().all())

    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        result = await self._session.execute(select(Muscle).where(Muscle.id == muscle_id))
        return result.scalars().one_or_none()

    async def get_by_name(self, name: str) -> Muscle | None:
        result = await self._session.execute(select(Muscle).where(Muscle.name == name))
        return result.scalars().one_or_none()

    async def add(self, muscle: Muscle) -> None:
        self._session.add(muscle)

    async def delete(self, muscle_id: int) -> None:
        await self._session.execute(delete(Muscle).where(Muscle.id == muscle_id))
