from __future__ import annotations

from src.domain.entities.exercise import Exercise
from src.domain.value_objects.coarse_muscle_group import CoarseMuscleGroup


class MuscleCoarseGroupMapper:
    """Маппинг тонких `muscles.name` в coarse-группы для окна восстановления 48ч."""

    BY_MUSCLE_NAME: dict[str, CoarseMuscleGroup] = {
        "chest": CoarseMuscleGroup.CHEST,
        "back": CoarseMuscleGroup.BACK,
        "traps": CoarseMuscleGroup.BACK,
        "rear_delts": CoarseMuscleGroup.SHOULDERS,
        "shoulders": CoarseMuscleGroup.SHOULDERS,
        "biceps": CoarseMuscleGroup.ARMS,
        "triceps": CoarseMuscleGroup.ARMS,
        "forearms": CoarseMuscleGroup.ARMS,
        "quadriceps": CoarseMuscleGroup.LEGS,
        "glutes": CoarseMuscleGroup.LEGS,
        "hamstrings": CoarseMuscleGroup.LEGS,
        "calves": CoarseMuscleGroup.LEGS,
        "adductors": CoarseMuscleGroup.LEGS,
        "hip_flexors": CoarseMuscleGroup.LEGS,
        "core": CoarseMuscleGroup.CORE,
        "obliques": CoarseMuscleGroup.CORE,
        "full_body": CoarseMuscleGroup.CORE,
    }

    @classmethod
    def groups_for_exercise(cls, exercise: Exercise) -> frozenset[str]:
        out: set[CoarseMuscleGroup] = set()
        if exercise.is_cardio:
            out.add(CoarseMuscleGroup.CARDIO)
        for muscle in exercise.muscles or []:
            name = (muscle.name or "").strip().lower()
            mapped = cls.BY_MUSCLE_NAME.get(name)
            if mapped:
                out.add(mapped)
        if not out and exercise.is_cardio:
            return frozenset({CoarseMuscleGroup.CARDIO.value})
        if not out:
            return frozenset({CoarseMuscleGroup.CORE.value})
        return frozenset(group.value for group in out)

    @classmethod
    def groups_for_exercises(cls, exercises: list[Exercise]) -> frozenset[str]:
        acc: set[str] = set()
        for exercise in exercises:
            acc |= cls.groups_for_exercise(exercise)
        return frozenset(acc)
