from __future__ import annotations

from src.application.workout.plan_management.models import WorkoutCycleProgressSummary
from src.domain.entities.training_plan import ScheduledWorkout, TrainingPlan


class WorkoutCycleProgressService:
    def build_summary(
        self,
        *,
        current_plan: TrainingPlan,
        current_workouts: list[ScheduledWorkout],
        previous_plan: TrainingPlan | None,
        previous_workouts: list[ScheduledWorkout],
        cycle_index: int,
        phase: str,
        workouts_per_week: int,
    ) -> WorkoutCycleProgressSummary:
        completed = sum(1 for item in current_workouts if item.is_completed)
        planned = len(current_workouts)
        completion_rate = round((completed / planned), 3) if planned else 0.0
        adherence_score = completion_rate

        previous_completed = sum(1 for item in previous_workouts if item.is_completed)
        novelty_ratio = self._novelty_ratio(current_workouts, previous_workouts)
        return WorkoutCycleProgressSummary(
            adherence_score=adherence_score,
            completion_rate=completion_rate,
            novelty_ratio=novelty_ratio,
            phase=phase,
            cycle_index=cycle_index,
            workouts_per_week=workouts_per_week,
            planned_workouts=planned,
            completed_workouts=completed,
            previous_completed_workouts=previous_completed,
        )

    @staticmethod
    def _novelty_ratio(
        current_workouts: list[ScheduledWorkout],
        previous_workouts: list[ScheduledWorkout],
    ) -> float:
        current_exercise_ids = {
            line.exercise_id
            for workout in current_workouts
            for line in workout.session_exercises
        }
        if not current_exercise_ids:
            return 0.0
        previous_exercise_ids = {
            line.exercise_id
            for workout in previous_workouts
            for line in workout.session_exercises
        }
        fresh = current_exercise_ids - previous_exercise_ids
        return round(len(fresh) / len(current_exercise_ids), 3)

