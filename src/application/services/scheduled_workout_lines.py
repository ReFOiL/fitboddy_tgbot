"""Строки запланированной тренировки из снимка `session_exercises`."""
from __future__ import annotations

from src.domain.entities.training_plan import ScheduledWorkout, ScheduledWorkoutExercise


def ordered_lines(sw: ScheduledWorkout) -> list[ScheduledWorkoutExercise]:
    return sorted(sw.session_exercises, key=lambda x: x.sort_order)


def workout_title(sw: ScheduledWorkout) -> str:
    n = len(sw.session_exercises)
    return f"Тренировка ({n} упр.)" if n else "Тренировка"
