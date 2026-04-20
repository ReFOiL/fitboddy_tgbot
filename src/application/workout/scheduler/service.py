from __future__ import annotations

from datetime import date, timedelta

import structlog

from src.application.workout.scheduler.models import (
    AnchorSelectionRequest,
    AbstractWorkoutScheduler,
    PlannedExerciseLine,
    RecoveryPenaltyRequest,
    RecoveryWindowRequest,
    ScheduledSessionItem,
    SessionCompositionRequest,
    WeeklyPatternRequest,
    WorkoutScheduleRequest,
)
from src.application.workout.scheduler.policies import (
    RecoveryOverlapScorer,
    RecoveryPenaltyPolicy,
    RecoveryWindowPolicy,
    WEEKLY_VOLUME_BY_WEEK,
    WeeklyPatternPolicy,
)
from src.application.workout.scheduler.strategies import (
    AnchorSelectionStrategy,
    SessionCompositionStrategy,
)
from src.domain.entities.exercise import Exercise

logger = structlog.get_logger()


class WorkoutScheduler(AbstractWorkoutScheduler):
    """
    Фасад планировщика тренировок.

    Оркестрирует политику оффсетов, выбор якорей, композицию сессии и recovery-политику.
    """

    def __init__(
        self,
        weekly_pattern_policy: WeeklyPatternPolicy | None = None,
        anchor_selection_strategy: AnchorSelectionStrategy | None = None,
        recovery_window_policy: RecoveryWindowPolicy | None = None,
        recovery_penalty_policy: RecoveryPenaltyPolicy | None = None,
        recovery_overlap_scorer: RecoveryOverlapScorer | None = None,
        session_composition_strategy: SessionCompositionStrategy | None = None,
    ) -> None:
        self._weekly_pattern = weekly_pattern_policy or WeeklyPatternPolicy()
        self._anchor_selection = anchor_selection_strategy or AnchorSelectionStrategy()
        self._recovery_window = recovery_window_policy or RecoveryWindowPolicy()
        self._recovery_penalty = recovery_penalty_policy or RecoveryPenaltyPolicy()
        self._recovery_overlap = recovery_overlap_scorer or RecoveryOverlapScorer()
        self._session_composition = session_composition_strategy or SessionCompositionStrategy(
            self._recovery_overlap
        )

    def build_schedule(self, request: WorkoutScheduleRequest) -> list[ScheduledSessionItem]:
        if not request.exercises or request.workouts_per_week < 1:
            return []
        workouts_per_week = min(request.workouts_per_week, 7)

        result: list[ScheduledSessionItem] = []
        for week in range(1, request.weeks + 1):
            week_volume = WEEKLY_VOLUME_BY_WEEK.get(week, 1.3)
            week_start = request.start_date + timedelta(days=(week - 1) * 7)
            offsets = self._weekly_pattern.choose_offsets(
                WeeklyPatternRequest(
                    workouts_per_week=workouts_per_week,
                    variation_seed=request.variation_seed,
                    week=week,
                )
            )
            anchors = self._anchor_selection.select_anchors(
                AnchorSelectionRequest(
                    exercises=request.exercises,
                    workouts_per_week=workouts_per_week,
                    week=week,
                    variation_seed=request.variation_seed,
                    goal=request.goal,
                )
            )

            for slot_index, (offset, anchor) in enumerate(zip(offsets, anchors, strict=False)):
                scheduled_for = week_start + timedelta(days=offset)
                recent_groups = self._recent_groups(result, scheduled_for)
                recipe = self._session_composition.compose_session(
                    SessionCompositionRequest(
                        pool=request.exercises,
                        anchor=anchor,
                        slot_index=slot_index,
                        week=week,
                        goal=request.goal,
                        variation_seed=request.variation_seed,
                        recent_groups=recent_groups,
                    )
                )
                lines = [self._prescribe(ex, sort_order=i + 1) for i, ex in enumerate(recipe.exercises)]
                final_volume = round(
                    week_volume
                    * self._recovery_penalty.calculate_penalty(
                        RecoveryPenaltyRequest(recent_groups=recent_groups, exercises=recipe.exercises)
                    ),
                    3,
                )

                result.append(
                    ScheduledSessionItem(
                        scheduled_for=scheduled_for,
                        week=week,
                        day_of_week=scheduled_for.weekday(),
                        volume_multiplier=final_volume,
                        lines=lines,
                    )
                )
        return result

    def _recent_groups(self, completed: list[ScheduledSessionItem], current_date: date) -> set[str]:
        snapshots = [(item.scheduled_for, [line.exercise for line in item.lines]) for item in completed]
        return self._recovery_window.collect_recent_groups(
            RecoveryWindowRequest(sessions=snapshots, current_date=current_date)
        )

    @staticmethod
    def _prescribe(exercise: Exercise, sort_order: int) -> PlannedExerciseLine:
        if exercise.is_cardio:
            return PlannedExerciseLine(
                exercise=exercise,
                sort_order=sort_order,
                sets=3,
                reps=None,
                duration_seconds=40,
                rest_seconds=30,
            )
        return PlannedExerciseLine(
            exercise=exercise,
            sort_order=sort_order,
            sets=3,
            reps=10,
            duration_seconds=None,
            rest_seconds=60,
        )
