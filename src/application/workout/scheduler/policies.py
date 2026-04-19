from __future__ import annotations

from datetime import date

from src.application.workout.muscles.mapper import MuscleCoarseGroupMapper
from src.domain.entities.exercise import Exercise

WEEKLY_VOLUME_BY_WEEK: dict[int, float] = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.3}


class WeeklyPatternPolicy:
    """Выбор оффсетов дней недели под число тренировок."""

    _DAY_PATTERNS: dict[int, list[list[int]]] = {
        1: [[0]],
        2: [[0, 3], [1, 4], [2, 5]],
        3: [[0, 2, 4], [1, 3, 5], [0, 3, 6]],
        4: [[0, 2, 4, 6], [0, 1, 3, 5], [1, 2, 4, 6]],
        5: [[0, 1, 3, 4, 6], [0, 2, 3, 5, 6], [1, 2, 4, 5, 6]],
        6: [[0, 1, 2, 3, 4, 5]],
        7: [[0, 1, 2, 3, 4, 5, 6]],
    }

    def offsets(self, workouts_per_week: int, variation_seed: int, *, week: int) -> list[int]:
        options = self._DAY_PATTERNS.get(workouts_per_week, [[0, 2, 4]])
        pick = (variation_seed + week - 1) % len(options)
        return list(options[pick])


class RecoveryPolicy:
    """Правила восстановления на горизонте 48 часов."""

    @staticmethod
    def recent_groups(
        sessions: list[tuple[date, list[Exercise]]],
        current_date: date,
    ) -> set[str]:
        lower = current_date.fromordinal(current_date.toordinal() - 2)
        out: set[str] = set()
        for scheduled_for, exercises in sessions:
            if lower <= scheduled_for < current_date:
                out |= MuscleCoarseGroupMapper.groups_for_exercises(exercises)
        return out

    @staticmethod
    def overlap_score(exercise: Exercise, recent_groups: set[str]) -> int:
        return len(MuscleCoarseGroupMapper.groups_for_exercise(exercise) & recent_groups)

    def penalty(self, recent_groups: set[str], exercises: list[Exercise]) -> float:
        if not recent_groups or not exercises:
            return 1.0
        session_groups = MuscleCoarseGroupMapper.groups_for_exercises(exercises)
        overlap = session_groups & recent_groups
        if not overlap:
            return 1.0
        return 0.9 if len(session_groups) <= len(overlap) or len(overlap) >= 2 else 1.0
