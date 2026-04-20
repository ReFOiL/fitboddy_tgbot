from __future__ import annotations

from src.domain.entities.training_plan import ScheduledWorkout


class AdherenceScorePolicy:
    def calculate(self, scheduled_workouts: list[ScheduledWorkout]) -> float:
        if not scheduled_workouts:
            return 1.0
        completed = sum(1 for item in scheduled_workouts if item.is_completed)
        return round(completed / len(scheduled_workouts), 3)

