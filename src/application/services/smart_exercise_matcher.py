"""
Подбор упражнений из каталога по ответам анкеты (без шаблонов тренировок).
"""
from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.matching import CatalogExerciseMatcher
from src.domain.entities.exercise import Exercise
from src.domain.entities.user_answer import UserAnswer


class SmartExerciseMatcher:
    """Фасад подбора упражнений по профилю пользователя."""

    def __init__(self, uow: UnitOfWork, catalog_matcher: CatalogExerciseMatcher | None = None) -> None:
        self._uow = uow
        self._catalog_matcher = catalog_matcher or CatalogExerciseMatcher()

    async def match(self, user_answers: list[UserAnswer], *, limit: int = 50) -> list[Exercise]:
        all_exercises = await self._uow.exercises.list_all()
        return self._catalog_matcher.match(all_exercises, user_answers, limit=limit)
