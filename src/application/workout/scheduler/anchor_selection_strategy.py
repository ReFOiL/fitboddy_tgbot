from __future__ import annotations

import random
import zlib

from src.application.workout.scheduler.models import AnchorSelectionRequest
from src.domain.entities.exercise import Exercise


class AnchorSelectionStrategy:
    """Выбор якорных упражнений недели."""

    def select_anchors(self, request: AnchorSelectionRequest) -> list[Exercise]:
        if not request.exercises:
            return []
        by_category = self._group_by_category(request.exercises)
        if len(by_category) == 1:
            only = list(by_category.values())[0]
            offset = ((request.week - 1) + (request.variation_seed % 7)) % len(only)
            return [only[(i + offset) % len(only)] for i in range(request.workouts_per_week)]

        categories = sorted(by_category.keys())
        goal_key = request.goal.value if request.goal is not None else ""
        goal_salt = zlib.crc32(goal_key.encode()) & 0xFFFFFFFF
        rotate_by = (request.variation_seed + goal_salt + request.week * 3) % len(categories)
        categories = categories[rotate_by:] + categories[:rotate_by]

        rng = random.Random((request.variation_seed ^ 0x85EBCA6B) + request.week * 7919)
        cursor: dict[str, int] = {cat: 0 for cat in by_category}
        used_ids: set[int] = set()
        result: list[Exercise] = []
        for i in range(request.workouts_per_week):
            cat = categories[(i + request.week - 1) % len(categories)]
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
        for exercise in exercises:
            by_category.setdefault(getattr(exercise, "workout_category", None) or "full_body", []).append(
                exercise
            )
        return by_category
