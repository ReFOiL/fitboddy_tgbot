from __future__ import annotations

from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


def get_default_templates() -> list[tuple[WorkoutTemplate, str | None]]:
    """
    Возвращает список кортежей (шаблон, имя оборудования) для сида.
    
    Связи `required_equipment` устанавливаются в WorkoutTemplateSeeder
    после получения Equipment из БД на основе имени оборудования.
    """
    return [
        (
            WorkoutTemplate(
                title="Кардио круговая — старт",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=0.8,
                workout_category="cardio",
            ),
            None,  # Без оборудования
        ),
        (
            WorkoutTemplate(
                title="Кардио интервальная — базовая",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.MEDIUM,
                days_per_week=3,
                intensity_factor=1.2,
                workout_category="cardio",
            ),
            "treadmill",
        ),
        (
            WorkoutTemplate(
                title="Силовая на все тело — новичок",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=1.0,
                workout_category="full_body",
            ),
            "dumbbells",
        ),
        (
            WorkoutTemplate(
                title="Силовая сплит — прогресс",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.MEDIUM,
                days_per_week=4,
                intensity_factor=1.5,
                workout_category="full_body",
            ),
            "barbell",
        ),
        (
            WorkoutTemplate(
                title="Выносливость — круговая",
                goal="endurance",
                difficulty=WorkoutDifficulty.MEDIUM,
                days_per_week=4,
                intensity_factor=1.2,
                workout_category="cardio",
            ),
            None,  # Без оборудования
        ),
        (
            WorkoutTemplate(
                title="Реабилитация — базовая мобилизация",
                goal="rehabilitation",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=2,
                intensity_factor=0.6,
                workout_category="full_body",
            ),
            "resistance_bands",
        ),
    ]
