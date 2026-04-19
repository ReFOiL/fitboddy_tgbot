from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta

from src.domain.entities.exercise import Exercise


@dataclass(slots=True)
class PlannedExerciseLine:
    exercise: Exercise
    sort_order: int
    sets: int | None
    reps: int | None
    duration_seconds: int | None
    rest_seconds: int | None


@dataclass(slots=True)
class ScheduledSessionItem:
    scheduled_for: date
    week: int
    day_of_week: int
    volume_multiplier: float
    lines: list[PlannedExerciseLine]


class AbstractWorkoutScheduler(ABC):
    """Контракт построения календаря тренировок из каталога упражнений."""

    @abstractmethod
    def schedule_month(
        self,
        exercises: list[Exercise],
        workouts_per_week: int,
        start_date: date,
        weeks: int = 4,
    ) -> list[ScheduledSessionItem]:
        ...


class WorkoutScheduler(AbstractWorkoutScheduler):
    """
    Распределение по дням на N недель: в каждый слот — мини-тренировка из нескольких упражнений.

    Round-robin по `exercise.workout_category`, прогрессия объёма по неделям.
    """

    _SESSION_SIZE = 6

    def schedule_month(
        self,
        exercises: list[Exercise],
        workouts_per_week: int,
        start_date: date,
        weeks: int = 4,
    ) -> list[ScheduledSessionItem]:
        if not exercises:
            return []
        if workouts_per_week < 1:
            return []
        workouts_per_week = min(workouts_per_week, 7)

        day_offsets = self._day_offsets(workouts_per_week)
        result: list[ScheduledSessionItem] = []
        volume_by_week = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.3}

        for week in range(1, weeks + 1):
            volume_multiplier = volume_by_week.get(week, 1.3)
            week_start = start_date + timedelta(days=(week - 1) * 7)
            anchors = self._select_weekly_anchor_exercises(exercises, workouts_per_week, week)

            for idx, offset in enumerate(day_offsets):
                if idx < len(anchors):
                    scheduled_for = week_start + timedelta(days=offset)
                    lines = self._build_session_lines(exercises, anchors, idx, week)
                    result.append(
                        ScheduledSessionItem(
                            scheduled_for=scheduled_for,
                            week=week,
                            day_of_week=scheduled_for.weekday(),
                            volume_multiplier=volume_multiplier,
                            lines=lines,
                        )
                    )
        return result

    def _build_session_lines(
        self,
        pool: list[Exercise],
        weekly_anchors: list[Exercise],
        slot_index: int,
        week: int,
    ) -> list[PlannedExerciseLine]:
        anchor = weekly_anchors[slot_index]
        by_cat = self._group_by_category(pool)
        categories = sorted(by_cat.keys())
        lines: list[PlannedExerciseLine] = [self._prescribe(anchor, 1)]
        used: set[int] = {anchor.id}
        anchor_cat = getattr(anchor, "workout_category", None) or "full_body"
        rotation = (slot_index + (week - 1)) % max(len(categories), 1)
        if anchor_cat in categories:
            base = (categories.index(anchor_cat) + 1) % max(len(categories), 1)
            start = (base + rotation) % max(len(categories), 1)
        else:
            start = rotation % max(len(categories), 1)
        order = 2
        cat_i = start
        safety = 0
        while len(lines) < self._SESSION_SIZE and safety < 40:
            safety += 1
            if not categories:
                break
            cat = categories[cat_i % len(categories)]
            cat_i += 1
            cand = next((e for e in by_cat[cat] if e.id not in used), None)
            if cand is None:
                continue
            used.add(cand.id)
            lines.append(self._prescribe(cand, order))
            order += 1
        return lines

    def _prescribe(self, ex: Exercise, sort_order: int) -> PlannedExerciseLine:
        if ex.is_cardio:
            return PlannedExerciseLine(
                exercise=ex,
                sort_order=sort_order,
                sets=3,
                reps=None,
                duration_seconds=40,
                rest_seconds=30,
            )
        return PlannedExerciseLine(
            exercise=ex,
            sort_order=sort_order,
            sets=3,
            reps=10,
            duration_seconds=None,
            rest_seconds=60,
        )

    def _group_by_category(self, exercises: list[Exercise]) -> dict[str, list[Exercise]]:
        by_category: dict[str, list[Exercise]] = {}
        for ex in exercises:
            cat = getattr(ex, "workout_category", None) or "full_body"
            by_category.setdefault(cat, []).append(ex)
        return by_category

    def _select_weekly_anchor_exercises(
        self, exercises: list[Exercise], workouts_per_week: int, week: int
    ) -> list[Exercise]:
        if not exercises:
            return []

        by_category = self._group_by_category(exercises)
        if len(by_category) == 1:
            lst = list(by_category.values())[0]
            off = (week - 1) % max(len(lst), 1)
            return [lst[(i + off) % len(lst)] for i in range(workouts_per_week)]

        result: list[Exercise] = []
        category_indices: dict[str, int] = {cat: 0 for cat in by_category}
        categories_list = sorted(by_category.keys())
        used_exercise_ids: set[int] = set()

        for i in range(workouts_per_week):
            category = categories_list[(i + week - 1) % len(categories_list)]
            in_cat = by_category[category]
            picked: Exercise | None = None
            start_idx = category_indices[category]
            for j in range(len(in_cat)):
                idx = (start_idx + j) % len(in_cat)
                candidate = in_cat[idx]
                if candidate.id not in used_exercise_ids:
                    picked = candidate
                    category_indices[category] = (idx + 1) % len(in_cat)
                    used_exercise_ids.add(candidate.id)
                    break
            if picked is None:
                idx = category_indices[category]
                picked = in_cat[idx % len(in_cat)]
                category_indices[category] = (idx + 1) % len(in_cat)
            result.append(picked)
        return result

    def _day_offsets(self, workouts_per_week: int) -> list[int]:
        patterns: dict[int, list[int]] = {
            1: [0],
            2: [0, 3],
            3: [0, 2, 4],
            4: [0, 2, 4, 6],
            5: [0, 1, 3, 4, 6],
            6: [0, 1, 2, 3, 4, 5],
            7: [0, 1, 2, 3, 4, 5, 6],
        }
        return patterns.get(workouts_per_week, [0, 2, 4])
