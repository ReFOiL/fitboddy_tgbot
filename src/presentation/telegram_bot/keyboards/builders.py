from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

MENU_QUESTIONNAIRE = "📝 Анкета"
MENU_WORKOUTS = "🏋️ Тренировки"


def reply_keyboard(options: list[str], row_width: int = 2) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    for i in range(0, len(options), row_width):
        rows.append([KeyboardButton(text=opt) for opt in options[i : i + row_width]])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def main_menu() -> ReplyKeyboardMarkup:
    options = [MENU_QUESTIONNAIRE, MENU_WORKOUTS]
    return reply_keyboard(options, row_width=2)
