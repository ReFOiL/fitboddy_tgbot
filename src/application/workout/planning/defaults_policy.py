from __future__ import annotations

from src.domain.value_objects.workout_profile import TrainingGoal, TrainingLevel


class PlanningDefaultsPolicy:
    def resolve_level(self, raw_level: str | None) -> TrainingLevel:
        if raw_level is None or not raw_level.strip():
            return TrainingLevel.INTERMEDIATE
        return TrainingLevel.from_raw(raw_level)

    def resolve_workouts_per_week(
        self,
        raw_workouts_per_week: int | None,
        *,
        level: TrainingLevel,
        goal: TrainingGoal,
        is_first_plan: bool,
        adherence_score: float,
        readiness_multiplier: float,
    ) -> int:
        if raw_workouts_per_week is not None and raw_workouts_per_week > 0:
            value = raw_workouts_per_week
        else:
            value = self._default_workouts_per_week(level=level, goal=goal)
        value = self._adjust_by_adherence(value=value, adherence_score=adherence_score, is_first_plan=is_first_plan)
        value = self._adjust_by_readiness(value=value, readiness_multiplier=readiness_multiplier)
        if is_first_plan:
            value = self._first_plan_cap(value=value, level=level, goal=goal)
        return min(7, max(1, value))

    @staticmethod
    def _default_workouts_per_week(*, level: TrainingLevel, goal: TrainingGoal) -> int:
        if level == TrainingLevel.BEGINNER:
            base = 3
        elif level == TrainingLevel.INTERMEDIATE:
            base = 4
        else:
            base = 5
        if goal in (TrainingGoal.WEIGHT_LOSS, TrainingGoal.ENDURANCE):
            base += 1
        if goal == TrainingGoal.REHABILITATION:
            base = min(base, 3)
        return base

    @staticmethod
    def _first_plan_cap(*, value: int, level: TrainingLevel, goal: TrainingGoal) -> int:
        if goal == TrainingGoal.REHABILITATION:
            return min(value, 3)
        if level == TrainingLevel.BEGINNER:
            return min(value, 4)
        if level == TrainingLevel.INTERMEDIATE:
            return min(value, 5)
        return min(value, 6)

    @staticmethod
    def _adjust_by_adherence(*, value: int, adherence_score: float, is_first_plan: bool) -> int:
        if is_first_plan:
            return value
        if adherence_score >= 0.8:
            return value + 1
        if adherence_score <= 0.45:
            return value - 1
        return value

    @staticmethod
    def _adjust_by_readiness(*, value: int, readiness_multiplier: float) -> int:
        if readiness_multiplier <= 0.9:
            return value - 1
        if readiness_multiplier >= 1.08:
            return value + 1
        return value
