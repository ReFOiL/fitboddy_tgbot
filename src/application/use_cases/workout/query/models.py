from __future__ import annotations

from dataclasses import dataclass

from src.application.workout.plan_management.models import WorkoutCycleProgressSummary
from src.domain.entities.exercise import Exercise
from src.domain.entities.training_plan import ScheduledWorkout, ScheduledWorkoutExercise, TrainingPlan
from src.domain.value_objects.workout_profile import ReflectionEnergy

@dataclass(slots=True)
class MyPlanViewData:
    user_id: int
    telegram_id: int
    plan: TrainingPlan
    progress: WorkoutCycleProgressSummary | None = None
    recent_difficulties: list[str] | None = None
    recent_energies: list[ReflectionEnergy] | None = None


@dataclass(slots=True)
class TodayWorkoutViewData:
    user_id: int
    telegram_id: int
    scheduled: ScheduledWorkout
    rows: list[ScheduledWorkoutExercise]


@dataclass(slots=True)
class ExerciseDetailViewData:
    user_id: int
    telegram_id: int
    scheduled: ScheduledWorkout
    workout_exercise: ScheduledWorkoutExercise
    exercise: Exercise


@dataclass(slots=True)
class CompletedTodayWorkoutData:
    user_id: int
    telegram_id: int
    scheduled_workout_id: int
    scheduled_for_iso: str
