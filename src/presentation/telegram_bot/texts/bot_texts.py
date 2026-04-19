from __future__ import annotations

from enum import StrEnum


class BotTexts(StrEnum):
    START_WELCOME = "Привет! Выбирай действие в меню ниже."

    WORKOUTS_REGISTER_FIRST = "Сначала зарегистрируйтесь через /start."
    WORKOUTS_COMPLETE_QUESTIONNAIRE = "Сначала пройдите анкету."
    WORKOUTS_USE_MY_PLAN = "План собирается из каталога упражнений. Откройте «Мой план» в меню или отправьте /myplan."
    WORKOUTS_EXITED = "Возвращаю в главное меню."

    PLAN_NO_PLAN = "Сначала пройдите анкету и получите план: нажмите «Тренировки» в меню."
    PLAN_HEADER = "📅 Ваш план на месяц"
    TODAY_NO_WORKOUT = "На сегодня тренировки нет. Отдыхайте! 💪"
    TODAY_HEADER = "🏋️ Тренировка на сегодня"
    EXERCISE_NO_EXERCISE = "Упражнение не найдено."
    DONE_ALREADY = "Эта тренировка уже отмечена выполненной."
    DONE_OK = "✅ Тренировка отмечена выполненной!"
    WORKOUT_NOT_FOUND = "Тренировка не найдена."
    WORKOUT_NOT_YOURS = "Это не ваша тренировка."
    WORKOUT_DETAIL_HEADER = "🏋️ Тренировка"
    EFFORT_PROMPT = "Как по ощущениям?"
    EFFORT_SAVED = "Спасибо, учтём в будущем."

    QUESTIONNAIRE_COMPLETED = "🎉 Анкета завершена!"
    QUESTIONNAIRE_FINISHED_PROMPT = "Анкета завершена. Что дальше?"
    QUESTIONNAIRE_LOAD_ERROR = "❌ Ошибка загрузки вопросов."
    QUESTIONNAIRE_UPDATED_RESTART = "Анкета обновилась. Запустите заново."
    QUESTIONNAIRE_SAVE_ERROR = "Не удалось сохранить ответ. Попробуйте еще раз."
    QUESTIONNAIRE_YES = "Да"
    QUESTIONNAIRE_NO = "Нет"
