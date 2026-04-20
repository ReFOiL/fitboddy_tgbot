"""Логика адаптации training_load_multiplier по фидбекам."""
from __future__ import annotations

import pytest

from src.application.workout.feedback.policy import (
    EffortNormalizationPolicy,
    TrainingLoadProgressionPolicy,
)


@pytest.mark.parametrize(
    "current,last3,expected",
    [
        (1.0, ["easy", "easy", "easy"], 1.1),
        (1.5, ["easy", "easy", "easy"], 1.5),
        (1.0, ["hard", "hard", "hard"], 0.9),
        (0.7, ["hard", "hard", "hard"], 0.7),
        (1.0, ["easy", "normal", "hard"], 1.0),
        (1.0, ["easy", "easy"], 1.0),
    ],
)
def test_next_training_load_multiplier(current: float, last3: list[str], expected: float) -> None:
    assert TrainingLoadProgressionPolicy().next_multiplier(current, last3) == pytest.approx(expected)


def test_normalize_effort() -> None:
    policy = EffortNormalizationPolicy()
    assert policy.normalize("ok") == "normal"
    assert policy.normalize("EASY") == "easy"
