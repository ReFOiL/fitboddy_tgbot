from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.workout_profile import EquipmentName, TrainingGoal, TrainingLevel, WorkoutLocation


@dataclass(slots=True)
class ExerciseMatchingProfile:
    allowed_equipment: set[EquipmentName]
    level: TrainingLevel
    workout_location: WorkoutLocation | None
    goal: TrainingGoal
