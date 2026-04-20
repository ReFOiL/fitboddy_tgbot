from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.contraindication import Contraindication
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle
from src.domain.entities.questionnaire import CustomQuestion
from src.infrastructure.database.seed_catalogs import (
    EXERCISE_CATALOG,
    CustomQuestionSeedCatalog,
)


class WorkoutMvpFixturesSeeder:
    """
    Фикстуры для MVP тренировок:
    - каталог из 60 упражнений (категории для планировщика; много вариантов без инвентаря)
    - video_url как ключ для MinIO (заглушки)
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def run(self) -> int:
        created = 0
        async with self._uow:
            created += await self._seed_muscles_and_contraindications()
            created += await self._seed_exercises()
            if created:
                await self._uow.commit()
        return created

    async def _get_or_create_muscle(self, name: str) -> Muscle:
        m = await self._uow.muscles.get_by_name(name)
        if m is not None:
            return m
        muscle = Muscle(name=name, sort_order=0)
        await self._uow.muscles.add(muscle)
        await self._uow.flush()
        return muscle

    async def _get_or_create_contraindication(self, name: str) -> Contraindication:
        c = await self._uow.contraindications.get_by_name(name)
        if c is not None:
            return c
        contra = Contraindication(name=name, sort_order=0)
        await self._uow.contraindications.add(contra)
        await self._uow.flush()
        return contra

    async def _seed_muscles_and_contraindications(self) -> int:
        added = 0
        muscle_names: set[str] = set()
        contra_names: set[str] = set()
        for row in EXERCISE_CATALOG:
            _, _, _, muscles, _, _, _, contras, _ = row
            muscle_names.update(muscles)
            contra_names.update(contras)
        for name in muscle_names:
            existing = await self._uow.muscles.get_by_name(name)
            if existing is None:
                await self._uow.muscles.add(Muscle(name=name, sort_order=0))
                await self._uow.flush()
                added += 1
        for name in contra_names:
            existing = await self._uow.contraindications.get_by_name(name)
            if existing is None:
                await self._uow.contraindications.add(Contraindication(name=name, sort_order=0))
                await self._uow.flush()
                added += 1
        return added

    async def _seed_exercises(self) -> int:
        added = 0
        for (
            name,
            description,
            video_url,
            muscle_names,
            equipment,
            difficulty,
            is_cardio,
            contra_names,
            workout_category,
        ) in EXERCISE_CATALOG:
            existing = await self._uow.exercises.get_by_name(name)
            if existing is not None:
                continue
            muscles = [await self._get_or_create_muscle(n) for n in muscle_names]
            contras = [await self._get_or_create_contraindication(n) for n in contra_names]
            exercise = Exercise(
                name=name,
                description=description,
                video_url=video_url,
                equipment=equipment,
                difficulty=difficulty,
                is_cardio=is_cardio,
                workout_category=workout_category,
            )
            exercise.muscles = muscles
            exercise.contraindications = contras
            await self._uow.exercises.add(exercise)
            await self._uow.flush()
            added += 1
        return added


class CustomQuestionSeeder:
    def __init__(
        self,
        uow: UnitOfWork,
        catalog: CustomQuestionSeedCatalog | None = None,
    ) -> None:
        self._uow = uow
        self._catalog = catalog or CustomQuestionSeedCatalog()

    async def run(self) -> int:
        async with self._uow:
            changes = 0
            changes += await self._ensure_questions(self._catalog.system_questions())
            changes += await self._ensure_mvp_custom_question()
            if changes:
                await self._uow.commit()
            return changes

    async def _ensure_questions(self, questions: list[CustomQuestion]) -> int:
        added = 0
        for question in questions:
            existing = await self._uow.custom_questions.get_by_key(question.key)
            if existing is None:
                await self._uow.custom_questions.add(question)
                added += 1
        return added

    async def _ensure_mvp_custom_question(self) -> int:
        if await self._uow.custom_questions.get_by_key("custom:health_notes") is not None:
            return 0
        await self._uow.custom_questions.add(self._catalog.mvp_custom_question())
        return 1
