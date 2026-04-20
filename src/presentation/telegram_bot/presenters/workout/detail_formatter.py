from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application.services.scheduled_workout_lines import ordered_lines, workout_title
from src.domain.entities.training_plan import ScheduledWorkout
from src.presentation.telegram_bot.presenters.workout.load_formatter import WorkoutLoadFormatter
from src.presentation.telegram_bot.texts import BotTexts


class WorkoutDetailFormatter:
    def format_workout(self, scheduled_workout: ScheduledWorkout) -> tuple[str, InlineKeyboardMarkup]:
        title = workout_title(scheduled_workout)
        volume = float(scheduled_workout.volume_multiplier or 1.0)
        ordered = ordered_lines(scheduled_workout)
        approx_minutes = self._estimate_session_minutes(multiplier=volume, exercise_count=len(ordered))
        lines = [
            BotTexts.WORKOUT_DETAIL_HEADER,
            "",
            title,
            f"Объём недели: ×{volume:.1f}",
            f"Упражнений: {len(ordered)} · Примерно {approx_minutes} мин",
            "",
        ]
        for i, workout_exercise in enumerate(ordered, start=1):
            name = workout_exercise.exercise.name if workout_exercise.exercise else "—"
            part = WorkoutLoadFormatter.format_volume_part(
                sets=workout_exercise.sets,
                reps=workout_exercise.reps,
                duration_seconds=workout_exercise.duration_seconds,
                multiplier=volume,
            )
            lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))

        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text=f"{i}. {workout_exercise.exercise.name if workout_exercise.exercise else '—'}",
                    callback_data=f"exercise:{scheduled_workout.id}:{i}",
                )
            ]
            for i, workout_exercise in enumerate(ordered, start=1)
        ]
        if not scheduled_workout.is_completed:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="✅ Выполнено",
                        callback_data=f"complete_workout:{scheduled_workout.id}",
                    )
                ]
            )
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def _estimate_session_minutes(*, multiplier: float, exercise_count: int) -> int:
        base_minutes = 5
        per_exercise_minutes = max(2, int(round(3 * multiplier)))
        return base_minutes + (exercise_count * per_exercise_minutes)
