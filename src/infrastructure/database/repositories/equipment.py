from sqlalchemy import delete, select

from src.application.interfaces.repositories import IEquipmentRepository
from src.domain.entities.equipment import Equipment
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class EquipmentRepository(SQLAlchemyRepository, IEquipmentRepository):
    async def list_all(self) -> list[Equipment]:
        result = await self._session.execute(select(Equipment).order_by(Equipment.name))
        return list(result.scalars().all())

    async def list_active(self) -> list[Equipment]:
        result = await self._session.execute(
            select(Equipment).where(Equipment.is_active.is_(True)).order_by(Equipment.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, equipment_id: int) -> Equipment | None:
        result = await self._session.execute(select(Equipment).where(Equipment.id == equipment_id))
        return result.scalars().one_or_none()

    async def get_by_name(self, name: str) -> Equipment | None:
        result = await self._session.execute(select(Equipment).where(Equipment.name == name))
        return result.scalars().one_or_none()

    async def add(self, equipment: Equipment) -> None:
        self._session.add(equipment)

    async def delete(self, equipment_id: int) -> None:
        await self._session.execute(delete(Equipment).where(Equipment.id == equipment_id))
