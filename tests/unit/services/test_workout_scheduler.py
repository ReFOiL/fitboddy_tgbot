"""Тесты для WorkoutScheduler (каталог упражнений, без шаблонов)."""
from __future__ import annotations

import pytest
from datetime import date, timedelta

from src.application.workout.scheduler import WorkoutScheduler
from src.application.workout.scheduler.models import PlannedExerciseLine
from src.domain.entities.exercise import Exercise


class TestWorkoutScheduler:
    @pytest.fixture
    def scheduler(self) -> WorkoutScheduler:
        return WorkoutScheduler()

    @pytest.fixture
    def sample_exercises(self) -> list[Exercise]:
        return [
            Exercise(
                id=1,
                name="FB1",
                workout_category="full_body",
                equipment="none",
                difficulty=2,
                is_cardio=False,
            ),
            Exercise(
                id=2,
                name="U1",
                workout_category="upper",
                equipment="none",
                difficulty=2,
                is_cardio=False,
            ),
            Exercise(
                id=3,
                name="L1",
                workout_category="lower",
                equipment="none",
                difficulty=2,
                is_cardio=False,
            ),
            Exercise(
                id=4,
                name="C1",
                workout_category="cardio",
                equipment="none",
                difficulty=1,
                is_cardio=True,
            ),
        ]

    def test_selects_anchor_count(
        self, scheduler: WorkoutScheduler, sample_exercises: list[Exercise]
    ) -> None:
        anchors = scheduler._anchor_selection.select(sample_exercises, 3, week=1)
        assert len(anchors) == 3

    def test_round_robin_by_category(
        self, scheduler: WorkoutScheduler, sample_exercises: list[Exercise]
    ) -> None:
        anchors = scheduler._anchor_selection.select(sample_exercises, 3, week=1)
        cats = [getattr(e, "workout_category", "") for e in anchors]
        assert len(set(cats)) >= 2

    def test_schedules_month_correctly(
        self, scheduler: WorkoutScheduler, sample_exercises: list[Exercise]
    ) -> None:
        workouts_per_week = 3
        start_date = date(2026, 2, 10)
        weeks = 4
        result = scheduler.schedule_month(sample_exercises, workouts_per_week, start_date, weeks)
        assert len(result) == workouts_per_week * weeks
        assert all(isinstance(s.lines[0], PlannedExerciseLine) for s in result)
        assert result[0].scheduled_for >= start_date
        assert result[-1].scheduled_for <= start_date + timedelta(days=weeks * 7)

    def test_progresses_volume_multiplier(
        self, scheduler: WorkoutScheduler, sample_exercises: list[Exercise]
    ) -> None:
        result = scheduler.schedule_month(sample_exercises, 2, date(2026, 2, 10), weeks=4)
        by_week: dict[int, list[float]] = {}
        for item in result:
            by_week.setdefault(item.week, []).append(item.volume_multiplier)
        assert by_week[1][0] == pytest.approx(1.0)
        assert by_week[2][0] == pytest.approx(1.1)
        assert by_week[3][0] == pytest.approx(1.2)
        assert by_week[4][0] == pytest.approx(1.3)

    def test_handles_single_category(self, scheduler: WorkoutScheduler) -> None:
        exercises = [
            Exercise(
                id=i,
                name=f"E{i}",
                workout_category="full_body",
                equipment="none",
                difficulty=1,
                is_cardio=False,
            )
            for i in range(1, 4)
        ]
        anchors = scheduler._anchor_selection.select(exercises, 3, week=1)
        assert len(anchors) == 3
