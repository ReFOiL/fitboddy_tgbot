from __future__ import annotations

import enum


class AnswerType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    BOOLEAN = "boolean"


class SystemQuestionType(str, enum.Enum):
    GOAL = "goal"
    LEVEL = "level"
    EQUIPMENT = "equipment"
    GENDER = "gender"
    AGE = "age"
    HEIGHT = "height"
    WEIGHT = "weight"
    ACTIVITY = "activity"
    WORKOUTS_PER_WEEK = "workouts_per_week"
    WORKOUT_LOCATION = "workout_location"
