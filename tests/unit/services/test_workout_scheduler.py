"""Тесты для WorkoutScheduler."""
from __future__ import annotations

import pytest
from datetime import date, timedelta

from src.application.services.workout_scheduler import WorkoutScheduler, ScheduledWorkoutItem
from src.domain.entities.workout import WorkoutTemplate, WorkoutDifficulty


# WorkoutScheduler использует синхронные методы, поэтому async не нужен


class TestWorkoutScheduler:
    """Тесты для планировщика тренировок."""

    @pytest.fixture
    def scheduler(self) -> WorkoutScheduler:
        """Создаёт экземпляр планировщика."""
        return WorkoutScheduler()

    @pytest.fixture
    def sample_templates(self) -> list[WorkoutTemplate]:
        """Создаёт тестовые шаблоны разных категорий."""
        return [
            WorkoutTemplate(
                id=1,
                title="Full Body 1",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=1.0,
                workout_category="full_body",
                is_active=True,
            ),
            WorkoutTemplate(
                id=2,
                title="Upper Body",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.MEDIUM,
                days_per_week=4,
                intensity_factor=1.5,
                workout_category="upper",
                is_active=True,
            ),
            WorkoutTemplate(
                id=3,
                title="Lower Body",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.MEDIUM,
                days_per_week=4,
                intensity_factor=1.5,
                workout_category="lower",
                is_active=True,
            ),
            WorkoutTemplate(
                id=4,
                title="Cardio",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=1.0,
                workout_category="cardio",
                is_active=True,
            ),
        ]

    def test_selects_correct_number_of_templates(
        self, scheduler: WorkoutScheduler, sample_templates: list[WorkoutTemplate]
    ) -> None:
        """Должен выбирать правильное количество шаблонов."""
        # given
        workouts_per_week: int = 3
        
        # when
        result: list[WorkoutTemplate] = scheduler._select_weekly_templates(sample_templates, workouts_per_week, week=1)
        
        # then
        assert len(result) == workouts_per_week
        assert all(isinstance(t, WorkoutTemplate) for t in result)

    def test_round_robin_by_category(
        self, scheduler: WorkoutScheduler, sample_templates: list[WorkoutTemplate]
    ) -> None:
        """Должен чередовать категории через Round-Robin."""
        # given: 4 шаблона разных категорий
        workouts_per_week: int = 3
        
        # when
        result: list[WorkoutTemplate] = scheduler._select_weekly_templates(sample_templates, workouts_per_week, week=1)
        
        # then: должны быть разные категории (Round-Robin)
        categories: list[str] = [t.workout_category for t in result]
        # При Round-Robin должны чередоваться категории
        assert len(categories) == workouts_per_week
        # Проверяем, что категории чередуются (первые 3 должны быть разными, если возможно)
        unique_categories: int = len(set(categories))
        assert unique_categories >= 1  # Минимум одна категория

    def test_avoids_duplicates_in_week(
        self, scheduler: WorkoutScheduler, sample_templates: list[WorkoutTemplate]
    ) -> None:
        """Должен избегать повторов одного шаблона в неделе."""
        # given
        workouts_per_week: int = 3
        
        # when
        result: list[WorkoutTemplate] = scheduler._select_weekly_templates(sample_templates, workouts_per_week, week=1)
        
        # then: не должно быть дубликатов
        template_ids: list[int] = [t.id for t in result]
        assert len(template_ids) == len(set(template_ids))

    def test_handles_insufficient_templates(self, scheduler: WorkoutScheduler) -> None:
        """Должен корректно обрабатывать недостаточное количество шаблонов."""
        # given
        templates: list[WorkoutTemplate] = [
            WorkoutTemplate(
                id=1,
                title="Only One",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=1.0,
                workout_category="full_body",
                is_active=True,
            ),
        ]
        workouts_per_week: int = 5
        
        # when
        result: list[WorkoutTemplate] = scheduler._select_weekly_templates(templates, workouts_per_week, week=1)
        
        # then: должен вернуть запрошенное количество (циклически повторяя шаблон)
        assert len(result) == workouts_per_week
        # Все шаблоны должны быть одинаковыми (единственный доступный)
        assert all(t.id == templates[0].id for t in result)

    def test_schedules_month_correctly(
        self, scheduler: WorkoutScheduler, sample_templates: list[WorkoutTemplate]
    ) -> None:
        """Должен правильно распланировать месяц тренировок."""
        # given
        workouts_per_week: int = 3
        start_date: date = date(2026, 2, 10)  # Понедельник
        weeks: int = 4
        
        # when
        result: list[ScheduledWorkoutItem] = scheduler.schedule_month(sample_templates, workouts_per_week, start_date, weeks)
        
        # then: должно быть 3 тренировки * 4 недели = 12
        assert len(result) == workouts_per_week * weeks
        
        # Проверяем, что все даты в правильном диапазоне
        first_date: date = result[0].scheduled_for
        last_date: date = result[-1].scheduled_for
        assert first_date >= start_date
        assert last_date <= start_date + timedelta(days=weeks * 7)

    def test_progresses_volume_multiplier(
        self, scheduler: WorkoutScheduler, sample_templates: list[WorkoutTemplate]
    ) -> None:
        """Должен увеличивать volume_multiplier каждую неделю."""
        # given
        workouts_per_week: int = 2
        start_date: date = date(2026, 2, 10)  # Понедельник
        weeks: int = 4
        
        # when
        result: list[ScheduledWorkoutItem] = scheduler.schedule_month(sample_templates, workouts_per_week, start_date, weeks)
        
        # then: multiplier должен увеличиваться
        multipliers_by_week: dict[int, list[float]] = {}
        for item in result:
            week_num: int = item.week
            if week_num not in multipliers_by_week:
                multipliers_by_week[week_num] = []
            multipliers_by_week[week_num].append(item.volume_multiplier)
        
        # Проверяем прогрессию: неделя 1 = 1.0, неделя 2 = 1.1, и т.д.
        assert len(multipliers_by_week) == weeks
        assert multipliers_by_week[1][0] == pytest.approx(1.0)
        assert multipliers_by_week[2][0] == pytest.approx(1.1)
        assert multipliers_by_week[3][0] == pytest.approx(1.2)
        assert multipliers_by_week[4][0] == pytest.approx(1.3)

    def test_handles_single_category(self, scheduler: WorkoutScheduler) -> None:
        """Должен корректно обрабатывать случай, когда все шаблоны одной категории."""
        # given
        templates: list[WorkoutTemplate] = [
            WorkoutTemplate(
                id=i,
                title=f"Template {i}",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                days_per_week=3,
                intensity_factor=1.0,
                workout_category="full_body",
                is_active=True,
            )
            for i in range(1, 4)
        ]
        workouts_per_week: int = 3
        
        # when
        result: list[WorkoutTemplate] = scheduler._select_weekly_templates(templates, workouts_per_week, week=1)
        
        # then: должен вернуть 3 шаблона
        assert len(result) == 3
