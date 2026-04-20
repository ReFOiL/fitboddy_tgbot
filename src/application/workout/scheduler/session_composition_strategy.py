from __future__ import annotations

import random
from dataclasses import dataclass

from src.application.workout.scheduler.models import (
    RecoveryOverlapScoreRequest,
    SessionCompositionRequest,
)
from src.application.workout.scheduler.policies import RecoveryOverlapScorer
from src.domain.entities.exercise import Exercise
from src.domain.value_objects.workout_profile import TrainingGoal


@dataclass(slots=True)
class SessionRecipe:
    exercises: list[Exercise]


class SessionCompositionStrategy:
    """Собирает состав одной тренировки вокруг якоря."""

    SESSION_SIZE_MIN = 4
    SESSION_SIZE_MAX = 7

    def __init__(self, overlap_scorer: RecoveryOverlapScorer) -> None:
        self._overlap_scorer = overlap_scorer

    def compose_session(self, request: SessionCompositionRequest) -> SessionRecipe:
        target = self._session_size(
            request.week, request.slot_index, request.goal, request.variation_seed
        )
        rng = self._rng(request.variation_seed, request.week, request.slot_index)
        by_cat = self._group_by_category(request.pool)
        categories = sorted(by_cat.keys())
        if not categories:
            return SessionRecipe(exercises=[])

        anchor = self._refine_anchor(anchor=request.anchor, pool=request.pool, request=request, rng=rng)
        exercises: list[Exercise] = [anchor]
        used_ids: set[int] = {anchor.id}
        start = self._next_category_start(
            categories, self._category(anchor), request.slot_index, request.week
        )
        cat_i = start
        safety = 0
        while len(exercises) < target and safety < 60:
            safety += 1
            category = categories[cat_i % len(categories)]
            cat_i += 1
            candidates = [e for e in by_cat[category] if e.id not in used_ids]
            if not candidates:
                continue
            candidates.sort(
                key=lambda exercise: (
                    self._overlap_scorer.score_overlap(
                        RecoveryOverlapScoreRequest(
                            exercise=exercise, recent_groups=request.recent_groups
                        )
                    ),
                    rng.random(),
                )
            )
            picked = candidates[0]
            used_ids.add(picked.id)
            exercises.append(picked)
        return SessionRecipe(exercises=exercises)

    def _session_size(
        self,
        week: int,
        slot_index: int,
        goal: TrainingGoal | None,
        variation_seed: int,
    ) -> int:
        mix = (variation_seed + week * 17 + slot_index * 5) & 0xFFFFFFFF
        span = self.SESSION_SIZE_MAX - self.SESSION_SIZE_MIN + 1
        count = self.SESSION_SIZE_MIN + (mix % span)
        if goal == TrainingGoal.WEIGHT_LOSS and (mix >> 4) % 4 == 0:
            count = max(self.SESSION_SIZE_MIN, count - 1)
        if goal in (TrainingGoal.MUSCLE_GAIN, TrainingGoal.MAINTENANCE) and (mix >> 5) % 5 == 0:
            count = min(self.SESSION_SIZE_MAX, count + 1)
        return max(self.SESSION_SIZE_MIN, min(self.SESSION_SIZE_MAX, count))

    @staticmethod
    def _rng(variation_seed: int, week: int, slot_index: int) -> random.Random:
        seed = (variation_seed ^ 0x9E3779B9) + week * 1009 + slot_index * 97
        return random.Random(seed & 0x7FFFFFFF)

    @staticmethod
    def _category(exercise: Exercise) -> str:
        return getattr(exercise, "workout_category", None) or "full_body"

    @classmethod
    def _group_by_category(cls, exercises: list[Exercise]) -> dict[str, list[Exercise]]:
        by_category: dict[str, list[Exercise]] = {}
        for exercise in exercises:
            by_category.setdefault(cls._category(exercise), []).append(exercise)
        return by_category

    @staticmethod
    def _next_category_start(categories: list[str], anchor_cat: str, slot_index: int, week: int) -> int:
        rotation = (slot_index + week - 1) % len(categories)
        if anchor_cat not in categories:
            return rotation
        base = (categories.index(anchor_cat) + 1) % len(categories)
        return (base + rotation) % len(categories)

    def _refine_anchor(
        self,
        anchor: Exercise,
        pool: list[Exercise],
        request: SessionCompositionRequest,
        rng: random.Random,
    ) -> Exercise:
        category = self._category(anchor)
        same_category = [exercise for exercise in pool if self._category(exercise) == category and exercise.id != anchor.id]
        if not same_category:
            return anchor
        scored = sorted(
            [anchor, *same_category],
            key=lambda exercise: (
                self._overlap_scorer.score_overlap(
                    RecoveryOverlapScoreRequest(
                        exercise=exercise,
                        recent_groups=request.recent_groups,
                    )
                ),
                rng.random(),
            ),
        )
        return scored[0]
