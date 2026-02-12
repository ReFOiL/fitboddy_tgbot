"""Админ-сервис: CRUD упражнений."""
from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.contraindication import Contraindication
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle


class ExerciseAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_all(self) -> list[Exercise]:
        async with self._uow:
            return await self._uow.exercises.list_all()

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        async with self._uow:
            return await self._uow.exercises.get_by_id(exercise_id)

    async def _resolve_muscles(self, muscle_ids: list[int]) -> list[Muscle]:
        if not muscle_ids:
            return []
        muscles: list[Muscle] = []
        for mid in muscle_ids:
            m = await self._uow.muscles.get_by_id(mid)
            if m is not None:
                muscles.append(m)
        return muscles

    async def _resolve_contraindications(self, contraindication_ids: list[int]) -> list[Contraindication]:
        if not contraindication_ids:
            return []
        contras: list[Contraindication] = []
        for cid in contraindication_ids:
            c = await self._uow.contraindications.get_by_id(cid)
            if c is not None:
                contras.append(c)
        return contras

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        video_url: str | None = None,
        muscle_ids: list[int] | None = None,
        equipment: str | None = None,
        is_cardio: bool = False,
        difficulty: int = 1,
        contraindication_ids: list[int] | None = None,
    ) -> Exercise:
        async with self._uow:
            existing = await self._uow.exercises.get_by_name(name)
            if existing is not None:
                raise ValueError(f"Exercise with name '{name}' already exists")
            muscles = await self._resolve_muscles(muscle_ids or [])
            contras = await self._resolve_contraindications(contraindication_ids or [])
            exercise = Exercise(
                name=name,
                description=description,
                video_url=video_url,
                equipment=equipment,
                is_cardio=is_cardio,
                difficulty=difficulty,
            )
            exercise.muscles = muscles
            exercise.contraindications = contras
            await self._uow.exercises.add(exercise)
            await self._uow.flush()
            await self._uow.commit()
            await self._uow.refresh(exercise)
        return exercise

    async def update(self, exercise_id: int, **updates: object) -> Exercise | None:
        async with self._uow:
            exercise = await self._uow.exercises.get_by_id(exercise_id)
            if exercise is None:
                return None
            muscle_ids_raw = updates.pop("muscle_ids", None)
            contraindication_ids_raw = updates.pop("contraindication_ids", None)
            for key, value in updates.items():
                if hasattr(exercise, key):
                    setattr(exercise, key, value)
            if muscle_ids_raw is not None and isinstance(muscle_ids_raw, list):
                muscle_ids = [x for x in muscle_ids_raw if isinstance(x, int)]
                exercise.muscles = await self._resolve_muscles(muscle_ids)
            if contraindication_ids_raw is not None and isinstance(contraindication_ids_raw, list):
                contraindication_ids = [x for x in contraindication_ids_raw if isinstance(x, int)]
                exercise.contraindications = await self._resolve_contraindications(contraindication_ids)
            await self._uow.commit()
            await self._uow.refresh(exercise)
        return exercise

    async def delete(self, exercise_id: int) -> bool:
        async with self._uow:
            exercise = await self._uow.exercises.get_by_id(exercise_id)
            if exercise is None:
                return False
            await self._uow.exercises.delete(exercise_id)
            await self._uow.commit()
        return True
