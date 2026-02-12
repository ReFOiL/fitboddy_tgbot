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
    MVP-распределение тренировок по дням на 4 недели.

    - фиксированный паттерн дней для workouts_per_week (1..7)
    - прогрессия объема +10% в неделю
    - шаблоны циклически распределяются по слотам
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

        slot_index = 0
        for week in range(1, weeks + 1):
            volume_multiplier = 1.0 + (week - 1) * 0.1
            week_start = start_date + timedelta(days=(week - 1) * 7)
            for offset in day_offsets:
                scheduled_for = week_start + timedelta(days=offset)
                template = templates[slot_index % len(templates)]
                slot_index += 1
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

