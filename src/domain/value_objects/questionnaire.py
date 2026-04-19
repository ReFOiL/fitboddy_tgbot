from __future__ import annotations

import enum


class AnswerType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    BOOLEAN = "boolean"


class SystemQuestionType(str, enum.Enum):
    """Логические ключи системной анкеты (суффикс после «system:» в БД)."""

    GOAL = "goal"
    LEVEL = "level"
    WORKOUT_LOCATION = "workout_location"
    EQUIPMENT = "equipment"
    WORKOUTS_PER_WEEK = "workouts_per_week"
    AGE = "age"
    GENDER = "gender"
