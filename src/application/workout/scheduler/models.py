from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from src.domain.entities.exercise import Exercise
from src.domain.value_objects.workout_profile import TrainingGoal, TrainingLevel


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


@dataclass(slots=True)
class WorkoutScheduleRequest:
    exercises: list[Exercise]
    workouts_per_week: int
    start_date: date
    weeks: int = 4
    goal: TrainingGoal | None = None
    level: TrainingLevel | None = None
    phase: str = "accumulation"
    cycle_index: int = 1
    adherence_score: float = 1.0
    readiness_multiplier: float = 1.0
    weekly_volume_by_week: dict[int, float] | None = None
    is_first_plan: bool = False
    variation_seed: int = 0


@dataclass(slots=True)
class WeeklyPatternRequest:
    workouts_per_week: int
    variation_seed: int
    week: int


@dataclass(slots=True)
class RecoveryWindowRequest:
    sessions: list[tuple[date, list[Exercise]]]
    current_date: date


@dataclass(slots=True)
class RecoveryPenaltyRequest:
    recent_groups: set[str]
    exercises: list[Exercise]


@dataclass(slots=True)
class RecoveryOverlapScoreRequest:
    exercise: Exercise
    recent_groups: set[str]


@dataclass(slots=True)
class AnchorSelectionRequest:
    exercises: list[Exercise]
    workouts_per_week: int
    week: int
    variation_seed: int
    goal: TrainingGoal | None


@dataclass(slots=True)
class SessionCompositionRequest:
    pool: list[Exercise]
    anchor: Exercise
    slot_index: int
    week: int
    goal: TrainingGoal | None
    variation_seed: int
    recent_groups: set[str]
    level: TrainingLevel | None = None
    is_first_plan: bool = False


class AbstractWorkoutScheduler(ABC):
    """Контракт построения календаря тренировок из каталога упражнений."""

    @abstractmethod
    def build_schedule(self, request: WorkoutScheduleRequest) -> list[ScheduledSessionItem]:
        ...
