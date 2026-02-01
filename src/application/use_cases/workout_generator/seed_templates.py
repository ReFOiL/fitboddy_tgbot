from __future__ import annotations

from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


def get_default_templates() -> list[WorkoutTemplate]:
    return [
        WorkoutTemplate(
            title="Кардио круговая — старт",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            equipment="none",
            days_per_week=3,
        ),
        WorkoutTemplate(
            title="Кардио интервальная — базовая",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.MEDIUM,
            equipment="treadmill",
            days_per_week=3,
        ),
        WorkoutTemplate(
            title="Силовая на все тело — новичок",
            goal="muscle_gain",
            difficulty=WorkoutDifficulty.LOW,
            equipment="dumbbells",
            days_per_week=3,
        ),
        WorkoutTemplate(
            title="Силовая сплит — прогресс",
            goal="muscle_gain",
            difficulty=WorkoutDifficulty.MEDIUM,
            equipment="barbell",
            days_per_week=4,
        ),
        WorkoutTemplate(
            title="Выносливость — круговая",
            goal="endurance",
            difficulty=WorkoutDifficulty.MEDIUM,
            equipment="none",
            days_per_week=4,
        ),
        WorkoutTemplate(
            title="Реабилитация — базовая мобилизация",
            goal="rehabilitation",
            difficulty=WorkoutDifficulty.LOW,
            equipment="resistance_bands",
            days_per_week=2,
        ),
    ]
