from __future__ import annotations

from src.application.workout.muscles.mapper import MuscleCoarseGroupMapper
from src.application.workout.scheduler.models import (
    RecoveryOverlapScoreRequest,
    RecoveryPenaltyRequest,
    RecoveryWindowRequest,
    WeeklyPatternRequest,
)

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

    def choose_offsets(self, request: WeeklyPatternRequest) -> list[int]:
        options = self._DAY_PATTERNS.get(request.workouts_per_week, [[0, 2, 4]])
        pick = (request.variation_seed + request.week - 1) % len(options)
        return list(options[pick])


class RecoveryWindowPolicy:
    """Правила восстановления на горизонте 48 часов."""

    def collect_recent_groups(self, request: RecoveryWindowRequest) -> set[str]:
        lower = request.current_date.fromordinal(request.current_date.toordinal() - 2)
        out: set[str] = set()
        for scheduled_for, exercises in request.sessions:
            if lower <= scheduled_for < request.current_date:
                out |= MuscleCoarseGroupMapper.groups_for_exercises(exercises)
        return out


class RecoveryOverlapScorer:
    def score_overlap(self, request: RecoveryOverlapScoreRequest) -> int:
        return len(
            MuscleCoarseGroupMapper.groups_for_exercise(request.exercise) & request.recent_groups
        )


class RecoveryPenaltyPolicy:
    def calculate_penalty(self, request: RecoveryPenaltyRequest) -> float:
        if not request.recent_groups or not request.exercises:
            return 1.0
        session_groups = MuscleCoarseGroupMapper.groups_for_exercises(request.exercises)
        overlap = session_groups & request.recent_groups
        if not overlap:
            return 1.0
        return 0.9 if len(session_groups) <= len(overlap) or len(overlap) >= 2 else 1.0
