from __future__ import annotations

from enum import StrEnum


class SystemQuestionKey(StrEnum):
    GOAL = "system:goal"
    LEVEL = "system:level"
    WORKOUT_LOCATION = "system:workout_location"
    EQUIPMENT = "system:equipment"
    WORKOUTS_PER_WEEK = "system:workouts_per_week"
