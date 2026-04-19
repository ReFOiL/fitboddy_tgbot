"""Админ-сервис: CRUD справочника противопоказаний."""
from __future__ import annotations

from typing import TypedDict

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.contraindication import Contraindication


class ContraindicationUpdates(TypedDict, total=False):
    name: str
    sort_order: int


class ContraindicationAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_all(self) -> list[Contraindication]:
        async with self._uow:
            return await self._uow.contraindications.list_all()

    async def get_by_id(self, contraindication_id: int) -> Contraindication | None:
        async with self._uow:
            return await self._uow.contraindications.get_by_id(contraindication_id)

    async def create(self, *, name: str, sort_order: int = 0) -> Contraindication:
        async with self._uow:
            existing = await self._uow.contraindications.get_by_name(name)
            if existing is not None:
                raise ValueError(f"Contraindication with name '{name}' already exists")
            contra = Contraindication(name=name, sort_order=sort_order)
            await self._uow.contraindications.add(contra)
            await self._uow.flush()
            await self._uow.commit()
        return contra

    async def update(self, contraindication_id: int, **kwargs: str | int) -> Contraindication | None:
        async with self._uow:
            contra = await self._uow.contraindications.get_by_id(contraindication_id)
            if contra is None:
                return None
            if "name" in kwargs and kwargs["name"] is not None:
                contra.name = kwargs["name"]
            if "sort_order" in kwargs and kwargs["sort_order"] is not None:
                contra.sort_order = kwargs["sort_order"]
            await self._uow.commit()
        return contra

    async def delete(self, contraindication_id: int) -> bool:
        async with self._uow:
            contra = await self._uow.contraindications.get_by_id(contraindication_id)
            if contra is None:
                return False
            await self._uow.contraindications.delete(contraindication_id)
            await self._uow.commit()
        return True
