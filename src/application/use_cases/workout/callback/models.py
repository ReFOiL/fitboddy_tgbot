from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.training_plan import ScheduledWorkout
from src.domain.value_objects.workout_profile import PerceivedEffort, ReflectionEnergy


@dataclass(slots=True)
class WorkoutDetailResult:
    user_id: int
    scheduled_workout: ScheduledWorkout


@dataclass(slots=True)
class WorkoutDetailRequest:
    tg_user_id: int
    scheduled_id: int


@dataclass(slots=True)
class CompleteWorkoutRequest:
    tg_user_id: int
    scheduled_id: int


@dataclass(slots=True)
class SaveEffortRequest:
    tg_user_id: int
    scheduled_id: int
    level: PerceivedEffort


@dataclass(slots=True)
class SaveReflectionRequest:
    tg_user_id: int
    scheduled_id: int
    energy: ReflectionEnergy


@dataclass(slots=True)
class ReplaceWorkoutExerciseRequest:
    tg_user_id: int
    scheduled_id: int
    index: int


@dataclass(slots=True)
class ReplaceWorkoutExerciseResult:
    user_id: int
    scheduled_id: int
    index: int
    previous_exercise_name: str
    replacement_exercise_name: str
