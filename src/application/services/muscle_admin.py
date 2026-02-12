"""Админ-сервис: CRUD справочника мышечных групп."""
from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.muscle import Muscle


class MuscleAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_all(self) -> list[Muscle]:
        async with self._uow:
            return await self._uow.muscles.list_all()

    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        async with self._uow:
            return await self._uow.muscles.get_by_id(muscle_id)

    async def create(self, *, name: str, sort_order: int = 0) -> Muscle:
        async with self._uow:
            existing = await self._uow.muscles.get_by_name(name)
            if existing is not None:
                raise ValueError(f"Muscle with name '{name}' already exists")
            muscle = Muscle(name=name, sort_order=sort_order)
            await self._uow.muscles.add(muscle)
            await self._uow.flush()
            await self._uow.commit()
        return muscle

    async def update(self, muscle_id: int, **kwargs: object) -> Muscle | None:
        async with self._uow:
            muscle = await self._uow.muscles.get_by_id(muscle_id)
            if muscle is None:
                return None
            if "name" in kwargs and kwargs["name"] is not None:
                muscle.name = kwargs["name"]
            if "sort_order" in kwargs and kwargs["sort_order"] is not None:
                muscle.sort_order = kwargs["sort_order"]
            await self._uow.commit()
        return muscle

    async def delete(self, muscle_id: int) -> bool:
        async with self._uow:
            muscle = await self._uow.muscles.get_by_id(muscle_id)
            if muscle is None:
                return False
            await self._uow.muscles.delete(muscle_id)
            await self._uow.commit()
        return True
