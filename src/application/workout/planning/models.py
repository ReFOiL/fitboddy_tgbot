from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.entities.exercise import Exercise
from src.domain.value_objects.workout_profile import TrainingGoal, TrainingLevel


@dataclass(slots=True)
class VariationSeedRequest:
    user_id: int
    anchor: date
    workouts_per_week: int
    goal: TrainingGoal
    exercises: list[Exercise]


@dataclass(slots=True)
class LoadScalingRequest:
    sets: int | None
    reps: int | None
    duration_seconds: int | None
    user_load: float


@dataclass(slots=True)
class PlanningContext:
    workouts_per_week: int
    goal: TrainingGoal
    level: TrainingLevel
    phase: str
    cycle_index: int
    anchor: date
    variation_seed: int
    adherence_score: float
    readiness_multiplier: float
    weekly_volume_by_week: dict[int, float]
    user_load: float
    is_first_plan: bool
