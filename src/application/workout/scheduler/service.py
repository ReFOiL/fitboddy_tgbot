from __future__ import annotations

from datetime import date, timedelta

import structlog

from src.application.workout.scheduler.models import (
    AbstractWorkoutScheduler,
    PlannedExerciseLine,
    ScheduledSessionItem,
)
from src.application.workout.scheduler.policies import (
    RecoveryPolicy,
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
        recovery_policy: RecoveryPolicy | None = None,
        session_composition_strategy: SessionCompositionStrategy | None = None,
    ) -> None:
        self._weekly_pattern = weekly_pattern_policy or WeeklyPatternPolicy()
        self._anchor_selection = anchor_selection_strategy or AnchorSelectionStrategy()
        self._recovery = recovery_policy or RecoveryPolicy()
        self._session_composition = session_composition_strategy or SessionCompositionStrategy(
            self._recovery
        )

    def schedule_month(
        self,
        exercises: list[Exercise],
        workouts_per_week: int,
        start_date: date,
        weeks: int = 4,
        *,
        goal: str | None = None,
        variation_seed: int = 0,
    ) -> list[ScheduledSessionItem]:
        if not exercises or workouts_per_week < 1:
            return []
        workouts_per_week = min(workouts_per_week, 7)

        result: list[ScheduledSessionItem] = []
        for week in range(1, weeks + 1):
            week_volume = WEEKLY_VOLUME_BY_WEEK.get(week, 1.3)
            week_start = start_date + timedelta(days=(week - 1) * 7)
            offsets = self._weekly_pattern.offsets(workouts_per_week, variation_seed, week=week)
            anchors = self._anchor_selection.select(
                exercises,
                workouts_per_week,
                week,
                variation_seed=variation_seed,
                goal=goal,
            )

            for slot_index, (offset, anchor) in enumerate(zip(offsets, anchors, strict=False)):
                scheduled_for = week_start + timedelta(days=offset)
                recent_groups = self._recent_groups(result, scheduled_for)
                recipe = self._session_composition.compose(
                    pool=exercises,
                    anchor=anchor,
                    slot_index=slot_index,
                    week=week,
                    goal=goal,
                    variation_seed=variation_seed,
                    recent_groups=recent_groups,
                )
                lines = [self._prescribe(ex, sort_order=i + 1) for i, ex in enumerate(recipe.exercises)]
                final_volume = round(week_volume * self._recovery.penalty(recent_groups, recipe.exercises), 3)

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

    def _recent_groups(self, completed: list[ScheduledSessionItem], current_date: date) -> set[str]:
        snapshots = [(item.scheduled_for, [line.exercise for line in item.lines]) for item in completed]
        return self._recovery.recent_groups(snapshots, current_date)
