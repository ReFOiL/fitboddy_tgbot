from sqlalchemy import delete, select

from src.application.interfaces.repositories import IContraindicationRepository
from src.domain.entities.contraindication import Contraindication
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class ContraindicationRepository(SQLAlchemyRepository, IContraindicationRepository):
    async def list_all(self) -> list[Contraindication]:
        result = await self._session.execute(
            select(Contraindication).order_by(Contraindication.sort_order, Contraindication.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, contraindication_id: int) -> Contraindication | None:
        result = await self._session.execute(
            select(Contraindication).where(Contraindication.id == contraindication_id)
        )
        return result.scalars().one_or_none()

    async def get_by_name(self, name: str) -> Contraindication | None:
        result = await self._session.execute(select(Contraindication).where(Contraindication.name == name))
        return result.scalars().one_or_none()

    async def add(self, contraindication: Contraindication) -> None:
        self._session.add(contraindication)

    async def delete(self, contraindication_id: int) -> None:
        await self._session.execute(delete(Contraindication).where(Contraindication.id == contraindication_id))
