"""
Подбор упражнений из каталога по ответам анкеты (без шаблонов тренировок).
"""
from __future__ import annotations

import structlog

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.exercise import Exercise
from src.domain.entities.user_answer import UserAnswer
from src.shared.utils.profile_answers import AnswerLookup, UserAnswerExtractor

logger = structlog.get_logger()

_LEVEL_MAX_DIFFICULTY: dict[str, int] = {
    "beginner": 2,
    "intermediate": 3,
    "advanced": 4,
}


class SmartExerciseMatcher:
    """Фильтрация и ранжирование упражнений каталога под профиль пользователя."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def match(self, user_answers: list[UserAnswer], *, limit: int = 50) -> list[Exercise]:
        if not user_answers:
            logger.warning("smart_exercise_matcher.no_answers")
            return []

        lookup = AnswerLookup(user_answers)
        all_exercises = await self._uow.exercises.list_all()
        if not all_exercises:
            logger.warning("smart_exercise_matcher.no_catalog")
            return []

        allowed_equipment = self._allowed_equipment_strings(user_answers)
        max_difficulty = _LEVEL_MAX_DIFFICULTY.get(lookup.get_str("system:level") or "", 4)
        location = lookup.get_str("system:workout_location")
        goal = lookup.get_str("system:goal") or ""

        candidates: list[Exercise] = []
        for ex in all_exercises:
            if not self._equipment_ok(ex, allowed_equipment):
                continue
            if ex.difficulty > max_difficulty:
                continue
            if location == "home" and (ex.equipment or "none") == "barbell":
                continue
            candidates.append(ex)

        if not candidates:
            logger.warning("smart_exercise_matcher.no_matches_after_filter")
            return []

        scored = [(ex, self._score(ex, goal, lookup)) for ex in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        result = [ex for ex, _ in scored[:limit]]
        logger.info(
            "smart_exercise_matcher.matched",
            catalog=len(all_exercises),
            candidates=len(candidates),
            returned=len(result),
        )
        return result

    def _allowed_equipment_strings(self, user_answers: list[UserAnswer]) -> set[str]:
        names: set[str] = {"none"}
        ans = UserAnswerExtractor.find_by_question_key(user_answers, "system:equipment")
        if not ans:
            return names
        for n in UserAnswerExtractor.extract_equipment_names(ans):
            if n:
                names.add(n)
        return names

    def _equipment_ok(self, ex: Exercise, allowed: set[str]) -> bool:
        need = (ex.equipment or "none").strip().lower()
        return need in allowed

    def _score(self, ex: Exercise, goal: str, lookup: AnswerLookup) -> int:
        score = 10
        if goal == "weight_loss" and ex.is_cardio:
            score += 8
        if goal in ("muscle_gain", "maintenance") and not ex.is_cardio:
            score += 5
        if goal == "endurance" and ex.is_cardio:
            score += 8
        loc = lookup.get_str("system:workout_location")
        if loc == "home" and (ex.equipment or "none") in ("none", "dumbbells"):
            score += 3
        return score
