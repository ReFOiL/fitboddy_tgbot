from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.value_objects.workout_profile import PerceivedEffort


class WorkoutEffortKeyboardBuilder:
    @staticmethod
    def build(scheduled_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Легко",
                        callback_data=f"effort:{PerceivedEffort.EASY}:{scheduled_id}",
                    ),
                    InlineKeyboardButton(
                        text="Нормально",
                        callback_data=f"effort:{PerceivedEffort.OK}:{scheduled_id}",
                    ),
                    InlineKeyboardButton(
                        text="Тяжело",
                        callback_data=f"effort:{PerceivedEffort.HARD}:{scheduled_id}",
                    ),
                ]
            ]
        )
