from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.workout_profile import PerceivedEffort


@dataclass(frozen=True, slots=True)
class SmartNudge:
    kind: str
    text: str


class WorkoutNudgePolicy:
    def build_nudge(self, recent_difficulties: list[str], latest_effort: PerceivedEffort) -> SmartNudge:
        hard_count = sum(1 for item in recent_difficulties[:3] if item == "hard")
        easy_count = sum(1 for item in recent_difficulties[:3] if item == "easy")
        if hard_count >= 2 or latest_effort == PerceivedEffort.HARD:
            return SmartNudge(
                kind="recovery",
                text="Подсказка: было тяжело. На этой неделе оставь 1 день полного восстановления и следи за сном.",
            )
        if easy_count >= 2 or latest_effort == PerceivedEffort.EASY:
            return SmartNudge(
                kind="progress",
                text="Подсказка: тренировка далась легко. На следующей неделе можно добавить интенсивность.",
            )
        return SmartNudge(
            kind="consistency",
            text="Подсказка: держи ритм. Стабильные 3-4 тренировки в неделю дадут лучший долгосрочный результат.",
        )

