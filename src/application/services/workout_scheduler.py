from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from src.domain.entities.workout import WorkoutTemplate


@dataclass(slots=True)
class ScheduledWorkoutItem:
    template: WorkoutTemplate
    scheduled_for: date
    week: int
    day_of_week: int
    volume_multiplier: float


class WorkoutScheduler:
    """
    Улучшенное распределение тренировок по дням на 4 недели.

    - фиксированный паттерн дней для workouts_per_week (1..7)
    - прогрессия объема +10% в неделю
    - Round-Robin по категориям тренировок для сбалансированности
    - Избегает повторов одного шаблона в неделю, если есть альтернативы
    """

    def schedule_month(
        self,
        templates: list[WorkoutTemplate],
        workouts_per_week: int,
        start_date: date,
        weeks: int = 4,
    ) -> list[ScheduledWorkoutItem]:
        if not templates:
            return []
        if workouts_per_week < 1:
            return []
        workouts_per_week = min(workouts_per_week, 7)

        day_offsets = self._day_offsets(workouts_per_week)
        result: list[ScheduledWorkoutItem] = []

        for week in range(1, weeks + 1):
            volume_multiplier = 1.0 + (week - 1) * 0.1
            week_start = start_date + timedelta(days=(week - 1) * 7)
            
            # Выбираем шаблоны для недели с Round-Robin по категориям
            weekly_templates = self._select_weekly_templates(templates, workouts_per_week, week)
            
            for idx, offset in enumerate(day_offsets):
                if idx < len(weekly_templates):
                    scheduled_for = week_start + timedelta(days=offset)
                    template = weekly_templates[idx]
                    result.append(
                        ScheduledWorkoutItem(
                            template=template,
                            scheduled_for=scheduled_for,
                            week=week,
                            day_of_week=scheduled_for.weekday(),
                            volume_multiplier=volume_multiplier,
                        )
                    )
        return result

    def _select_weekly_templates(
        self, templates: list[WorkoutTemplate], workouts_per_week: int, week: int
    ) -> list[WorkoutTemplate]:
        """
        Выбрать шаблоны для недели с Round-Robin по категориям.

        Группирует шаблоны по workout_category и выбирает по одному из каждой категории по очереди.
        """
        if not templates:
            return []

        # Группируем по категориям
        by_category: dict[str, list[WorkoutTemplate]] = {}
        for template in templates:
            category = getattr(template, "workout_category", "full_body") or "full_body"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(template)

        # Если категория одна, просто циклически распределяем
        if len(by_category) == 1:
            category_templates = list(by_category.values())[0]
            result = []
            for i in range(workouts_per_week):
                result.append(category_templates[i % len(category_templates)])
            return result

        # Round-Robin по категориям
        result: list[WorkoutTemplate] = []
        category_indices: dict[str, int] = {cat: 0 for cat in by_category.keys()}
        categories_list = list(by_category.keys())
        used_template_ids: set[int] = set()

        for i in range(workouts_per_week):
            category = categories_list[i % len(categories_list)]
            templates_in_category = by_category[category]
            
            # Ищем шаблон, который еще не использовался в этой неделе
            template = None
            start_idx = category_indices[category]
            for j in range(len(templates_in_category)):
                idx = (start_idx + j) % len(templates_in_category)
                candidate = templates_in_category[idx]
                if candidate.id not in used_template_ids:
                    template = candidate
                    category_indices[category] = (idx + 1) % len(templates_in_category)
                    used_template_ids.add(candidate.id)
                    break
            
            # Если все шаблоны категории использованы, берем следующий по кругу
            if template is None:
                idx = category_indices[category]
                template = templates_in_category[idx % len(templates_in_category)]
                category_indices[category] = (idx + 1) % len(templates_in_category)
            
            result.append(template)

        return result

    def _day_offsets(self, workouts_per_week: int) -> list[int]:
        patterns: dict[int, list[int]] = {
            1: [0],
            2: [0, 3],
            3: [0, 2, 4],
            4: [0, 2, 4, 6],
            5: [0, 1, 3, 4, 6],
            6: [0, 1, 2, 3, 4, 5],
            7: [0, 1, 2, 3, 4, 5, 6],
        }
        return patterns.get(workouts_per_week, [0, 2, 4])

