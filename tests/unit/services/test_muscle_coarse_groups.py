"""Грубые мышечные зоны для планировщика."""
from __future__ import annotations

from src.application.workout.muscles.mapper import MuscleCoarseGroupMapper
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle


def _ex(name: str, muscles: list[str], *, cardio: bool = False) -> Exercise:
    ex = Exercise(
        id=1,
        name="t",
        workout_category="lower",
        equipment="none",
        difficulty=1,
        is_cardio=cardio,
    )
    ex.muscles = [Muscle(name=m, sort_order=0) for m in muscles]
    return ex


def test_quads_map_to_legs() -> None:
    g = MuscleCoarseGroupMapper.groups_for_exercise(_ex("x", ["quadriceps", "glutes"]))
    assert "legs" in g
    assert "cardio" not in g


def test_cardio_flag_adds_cardio() -> None:
    g = MuscleCoarseGroupMapper.groups_for_exercise(_ex("x", ["core"], cardio=True))
    assert "cardio" in g
    assert "core" in g
