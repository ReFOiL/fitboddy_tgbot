from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

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
        *,
        goal: str | None = None,
        variation_seed: int = 0,
    ) -> list[ScheduledSessionItem]:
        ...
