from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkoutCycleProgressSummary:
    adherence_score: float
    completion_rate: float
    novelty_ratio: float
    phase: str
    cycle_index: int
    workouts_per_week: int
    planned_workouts: int
    completed_workouts: int
    previous_completed_workouts: int

