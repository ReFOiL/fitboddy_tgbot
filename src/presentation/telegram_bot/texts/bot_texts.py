from __future__ import annotations

from enum import StrEnum


class BotTexts(StrEnum):
    START_WELCOME = "Привет! Выбирай действие в меню ниже."

    WORKOUTS_REGISTER_FIRST = "Сначала зарегистрируйтесь через /start."
    WORKOUTS_COMPLETE_QUESTIONNAIRE = "Сначала пройдите анкету."
    WORKOUTS_NO_TEMPLATES = "Пока нет шаблонов тренировок. Попробуйте позже."
    WORKOUTS_NO_MATCH = "Не удалось подобрать тренировки под вашу анкету."
    WORKOUTS_EXITED = "Возвращаю в главное меню."

    QUESTIONNAIRE_COMPLETED = "🎉 Анкета завершена!"
    QUESTIONNAIRE_FINISHED_PROMPT = "Анкета завершена. Что дальше?"
    QUESTIONNAIRE_LOAD_ERROR = "❌ Ошибка загрузки вопросов."
    QUESTIONNAIRE_UPDATED_RESTART = "Анкета обновилась. Запустите заново."
    QUESTIONNAIRE_SAVE_ERROR = "Не удалось сохранить ответ. Попробуйте еще раз."
    QUESTIONNAIRE_YES = "Да"
    QUESTIONNAIRE_NO = "Нет"
