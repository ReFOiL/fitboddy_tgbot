from __future__ import annotations

import random
import zlib
from dataclasses import dataclass

from src.application.workout.scheduler.policies import RecoveryPolicy
from src.domain.entities.exercise import Exercise


class AnchorSelectionStrategy:
    """Выбор якорных упражнений недели."""

    def select(
        self,
        exercises: list[Exercise],
        workouts_per_week: int,
        week: int,
        *,
        variation_seed: int,
        goal: str | None,
    ) -> list[Exercise]:
        if not exercises:
            return []
        by_category = self._group_by_category(exercises)
        if len(by_category) == 1:
            only = list(by_category.values())[0]
            offset = ((week - 1) + (variation_seed % 7)) % len(only)
            return [only[(i + offset) % len(only)] for i in range(workouts_per_week)]

        categories = sorted(by_category.keys())
        goal_salt = zlib.crc32((goal or "").encode()) & 0xFFFFFFFF
        rotate_by = (variation_seed + goal_salt + week * 3) % len(categories)
        categories = categories[rotate_by:] + categories[:rotate_by]

        rng = random.Random((variation_seed ^ 0x85EBCA6B) + week * 7919)
        cursor: dict[str, int] = {cat: 0 for cat in by_category}
        used_ids: set[int] = set()
        result: list[Exercise] = []
        for i in range(workouts_per_week):
            cat = categories[(i + week - 1) % len(categories)]
            result.append(self._pick_from_category(by_category[cat], cursor, cat, used_ids, rng))
        return result

    @staticmethod
    def _pick_from_category(
        items: list[Exercise],
        cursor_by_category: dict[str, int],
        category: str,
        used_ids: set[int],
        rng: random.Random,
    ) -> Exercise:
        start_idx = cursor_by_category[category]
        fresh = [e for e in items if e.id not in used_ids]
        if fresh:
            picked = rng.choice(fresh)
            cursor_by_category[category] = (items.index(picked) + 1) % len(items)
            used_ids.add(picked.id)
            return picked

        for step in range(len(items)):
            idx = (start_idx + step) % len(items)
            candidate = items[idx]
            if candidate.id not in used_ids:
                cursor_by_category[category] = (idx + 1) % len(items)
                used_ids.add(candidate.id)
                return candidate

        picked = items[start_idx % len(items)]
        cursor_by_category[category] = (start_idx + 1) % len(items)
        return picked

    @staticmethod
    def _group_by_category(exercises: list[Exercise]) -> dict[str, list[Exercise]]:
        by_category: dict[str, list[Exercise]] = {}
        for ex in exercises:
            by_category.setdefault(getattr(ex, "workout_category", None) or "full_body", []).append(ex)
        return by_category


@dataclass(slots=True)
class SessionRecipe:
    exercises: list[Exercise]


class SessionCompositionStrategy:
    """Собирает состав одной тренировки вокруг якоря."""

    SESSION_SIZE_MIN = 4
    SESSION_SIZE_MAX = 7

    def __init__(self, recovery_policy: RecoveryPolicy) -> None:
        self._recovery = recovery_policy

    def compose(
        self,
        *,
        pool: list[Exercise],
        anchor: Exercise,
        slot_index: int,
        week: int,
        goal: str | None,
        variation_seed: int,
        recent_groups: set[str],
    ) -> SessionRecipe:
        target = self._session_size(week, slot_index, goal, variation_seed)
        rng = self._rng(variation_seed, week, slot_index)
        by_cat = self._group_by_category(pool)
        categories = sorted(by_cat.keys())
        if not categories:
            return SessionRecipe(exercises=[])

        anchor = self._refine_anchor(anchor, pool, recent_groups, rng)
        exercises: list[Exercise] = [anchor]
        used_ids: set[int] = {anchor.id}
        start = self._next_category_start(categories, self._category(anchor), slot_index, week)
        cat_i = start
        safety = 0
        while len(exercises) < target and safety < 60:
            safety += 1
            category = categories[cat_i % len(categories)]
            cat_i += 1
            candidates = [e for e in by_cat[category] if e.id not in used_ids]
            if not candidates:
                continue
            candidates.sort(key=lambda ex: (self._recovery.overlap_score(ex, recent_groups), rng.random()))
            picked = candidates[0]
            used_ids.add(picked.id)
            exercises.append(picked)
        return SessionRecipe(exercises=exercises)

    def _session_size(self, week: int, slot_index: int, goal: str | None, variation_seed: int) -> int:
        mix = (variation_seed + week * 17 + slot_index * 5) & 0xFFFFFFFF
        span = self.SESSION_SIZE_MAX - self.SESSION_SIZE_MIN + 1
        n = self.SESSION_SIZE_MIN + (mix % span)
        if goal == "weight_loss" and (mix >> 4) % 4 == 0:
            n = max(self.SESSION_SIZE_MIN, n - 1)
        if goal in ("muscle_gain", "maintenance") and (mix >> 5) % 5 == 0:
            n = min(self.SESSION_SIZE_MAX, n + 1)
        return max(self.SESSION_SIZE_MIN, min(self.SESSION_SIZE_MAX, n))

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
        for ex in exercises:
            by_category.setdefault(cls._category(ex), []).append(ex)
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
        recent_groups: set[str],
        rng: random.Random,
    ) -> Exercise:
        category = self._category(anchor)
        same_category = [e for e in pool if self._category(e) == category and e.id != anchor.id]
        if not same_category:
            return anchor
        scored = sorted(
            [anchor, *same_category],
            key=lambda ex: (self._recovery.overlap_score(ex, recent_groups), rng.random()),
        )
        return scored[0]
