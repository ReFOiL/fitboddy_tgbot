from __future__ import annotations

from src.application.workout.matching.models import ExerciseMatchingProfile
from src.domain.entities.user_answer import UserAnswer
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import (
    EquipmentName,
    TrainingGoal,
    TrainingLevel,
    WorkoutLocation,
)
from src.shared.utils.profile_answers import AnswerLookup, UserAnswerExtractor


class ExerciseMatchingProfileFactory:
    def build_profile(self, user_answers: list[UserAnswer]) -> ExerciseMatchingProfile:
        lookup = AnswerLookup(user_answers)
        workout_location = WorkoutLocation.from_raw(lookup.get_str(SystemQuestionKey.WORKOUT_LOCATION))
        return ExerciseMatchingProfile(
            allowed_equipment=self._allowed_equipment(user_answers, workout_location=workout_location),
            level=TrainingLevel.from_raw(lookup.get_str(SystemQuestionKey.LEVEL)),
            workout_location=workout_location,
            goal=TrainingGoal.from_raw(lookup.get_str(SystemQuestionKey.GOAL)),
        )

    @staticmethod
    def _allowed_equipment(
        user_answers: list[UserAnswer], *, workout_location: WorkoutLocation | None
    ) -> set[EquipmentName]:
        names: set[EquipmentName] = {EquipmentName.NONE}
        answer = UserAnswerExtractor.find_by_question_key(
            user_answers, SystemQuestionKey.EQUIPMENT
        )
        if answer:
            for equipment_name in UserAnswerExtractor.extract_equipment_names(answer):
                parsed = EquipmentName.from_raw(equipment_name)
                if parsed is not None:
                    names.add(parsed)
        if len(names) > 1:
            return names
        if workout_location == WorkoutLocation.HOME:
            return {
                EquipmentName.NONE,
                EquipmentName.DUMBBELLS,
                EquipmentName.RESISTANCE_BANDS,
                EquipmentName.KETTLEBELL,
            }
        if workout_location == WorkoutLocation.GYM:
            return {
                EquipmentName.NONE,
                EquipmentName.DUMBBELLS,
                EquipmentName.BARBELL,
                EquipmentName.RESISTANCE_BANDS,
                EquipmentName.KETTLEBELL,
                EquipmentName.TREADMILL,
                EquipmentName.OTHER,
            }
        return set(EquipmentName)
