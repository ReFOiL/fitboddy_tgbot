from __future__ import annotations

from src.application.workout.matching.models import ExerciseMatchingProfile
from src.domain.entities.exercise import Exercise
from src.domain.value_objects.workout_profile import EquipmentName, TrainingGoal, WorkoutLocation


class ExerciseScoringPolicy:
    def score(self, exercise: Exercise, profile: ExerciseMatchingProfile) -> int:
        score = 10
        if profile.goal == TrainingGoal.WEIGHT_LOSS and exercise.is_cardio:
            score += 8
        if profile.goal in (TrainingGoal.MUSCLE_GAIN, TrainingGoal.MAINTENANCE) and not exercise.is_cardio:
            score += 5
        if profile.goal == TrainingGoal.ENDURANCE and exercise.is_cardio:
            score += 8
        equipment = EquipmentName.from_raw(exercise.equipment) or EquipmentName.NONE
        if profile.workout_location == WorkoutLocation.HOME and equipment in (
            EquipmentName.NONE,
            EquipmentName.DUMBBELLS,
        ):
            score += 3
        return score
