from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class WorkoutReflectionKeyboardBuilder:
    @staticmethod
    def build(scheduled_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Энергии мало", callback_data=f"reflect:low:{scheduled_id}"),
                    InlineKeyboardButton(text="Нормально", callback_data=f"reflect:ok:{scheduled_id}"),
                    InlineKeyboardButton(text="Много энергии", callback_data=f"reflect:high:{scheduled_id}"),
                ]
            ]
        )

