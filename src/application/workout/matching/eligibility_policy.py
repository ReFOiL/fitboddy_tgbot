from __future__ import annotations

from src.application.workout.matching.models import ExerciseMatchingProfile
from src.domain.entities.exercise import Exercise
from src.domain.value_objects.workout_profile import EquipmentName, WorkoutLocation


class ExerciseEligibilityPolicy:
    def is_eligible(self, exercise: Exercise, profile: ExerciseMatchingProfile) -> bool:
        if not self._equipment_ok(exercise, profile.allowed_equipment):
            return False
        if exercise.difficulty > int(profile.level):
            return False
        if profile.workout_location == WorkoutLocation.HOME and self._normalize_equipment(exercise) == EquipmentName.BARBELL:
            return False
        return True

    @staticmethod
    def _equipment_ok(exercise: Exercise, allowed_equipment: set[EquipmentName]) -> bool:
        required = ExerciseEligibilityPolicy._normalize_equipment(exercise)
        return required in allowed_equipment

    @staticmethod
    def _normalize_equipment(exercise: Exercise) -> EquipmentName:
        return EquipmentName.from_raw(exercise.equipment) or EquipmentName.NONE
