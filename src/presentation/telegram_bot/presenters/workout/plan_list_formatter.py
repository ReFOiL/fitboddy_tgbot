from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application.services.scheduled_workout_lines import workout_title
from src.domain.entities.training_plan import TrainingPlan
from src.presentation.telegram_bot.texts import BotTexts


class WorkoutPlanListFormatter:
    def format_plan(self, plan: TrainingPlan) -> tuple[str, InlineKeyboardMarkup | None]:
        lines = [BotTexts.PLAN_HEADER, ""]
        rows: list[list[InlineKeyboardButton]] = []
        for workout in sorted(plan.scheduled_workouts, key=lambda item: item.scheduled_for):
            title = workout_title(workout)
            done = " ✅" if workout.is_completed else ""
            lines.append(f"{workout.scheduled_for:%d.%m} — {title}{done}")
            label = f"{workout.scheduled_for:%d.%m} {title}"[:60]
            rows.append([InlineKeyboardButton(text=label, callback_data=f"workout:{workout.id}")])
        markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
        return "\n".join(lines), markup
