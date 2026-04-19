"""Планировщик: окно 48 ч и штраф за пересечение мышечных зон."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.application.workout.scheduler.models import (
    PlannedExerciseLine,
    ScheduledSessionItem,
)
from src.application.workout.scheduler import WorkoutScheduler
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle


def _ex(
    eid: int,
    name: str,
    cat: str,
    muscle_names: list[str],
    *,
    cardio: bool = False,
) -> Exercise:
    ex = Exercise(
        id=eid,
        name=name,
        workout_category=cat,
        equipment="none",
        difficulty=2,
        is_cardio=cardio,
    )
    ex.muscles = [Muscle(name=m, sort_order=0) for m in muscle_names]
    return ex


def test_recent_coarse_groups_excludes_same_day() -> None:
    s = WorkoutScheduler()
    mon = date(2026, 4, 6)
    leg = _ex(1, "l", "lower", ["quadriceps"])
    line = PlannedExerciseLine(
        exercise=leg,
        sort_order=1,
        sets=3,
        reps=10,
        duration_seconds=None,
        rest_seconds=60,
    )
    prev = ScheduledSessionItem(
        scheduled_for=mon,
        week=1,
        day_of_week=0,
        volume_multiplier=1.0,
        lines=[line],
    )
    wed = mon + timedelta(days=2)
    recent = s._recent_groups([prev], wed)
    assert "legs" in recent


def test_recovery_penalty_when_overlap() -> None:
    s = WorkoutScheduler()
    leg = _ex(1, "l", "lower", ["quadriceps", "glutes"])
    line = PlannedExerciseLine(
        exercise=leg,
        sort_order=1,
        sets=3,
        reps=10,
        duration_seconds=None,
        rest_seconds=60,
    )
    recent = {"legs", "core"}
    assert s._recovery.penalty(recent, [line.exercise]) == pytest.approx(0.9)


def test_recovery_no_penalty_when_disjoint() -> None:
    s = WorkoutScheduler()
    chest = _ex(1, "c", "upper", ["chest"])
    line = PlannedExerciseLine(
        exercise=chest,
        sort_order=1,
        sets=3,
        reps=10,
        duration_seconds=None,
        rest_seconds=60,
    )
    recent = {"legs"}
    assert s._recovery.penalty(recent, [line.exercise]) == pytest.approx(1.0)
