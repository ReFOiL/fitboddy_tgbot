from __future__ import annotations

from collections import defaultdict

from src.application.use_cases.workout_generator.simple_matcher import MatchedWorkout


class WorkoutPlanPresenter:
    def format_plan(self, items: list[MatchedWorkout]) -> str:
        weeks: dict[int, list[str]] = defaultdict(list)
        for item in items:
            weeks[item.week].append(item.template.title)

        lines: list[str] = []
        for week in sorted(weeks.keys()):
            lines.append(f"Неделя {week}:")
            for title in weeks[week]:
                lines.append(f"- {title}")
        return "\n".join(lines)
