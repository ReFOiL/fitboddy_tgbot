from __future__ import annotations

from enum import StrEnum


class BotTexts(StrEnum):
    START_WELCOME = (
        "Привет! Я Fitboddy 🤝\n"
        "Помогу собрать умный план и вести тебя по тренировкам.\n\n"
        "Выбирайте действия кнопками внизу экрана.\n"
        "После тренировки отмечайте «✅ Выполнено», чтобы я точнее "
        "адаптировал следующую неделю."
    )

    WORKOUTS_REGISTER_FIRST = "Сначала нажмите «Старт», чтобы зарегистрироваться."
    WORKOUTS_COMPLETE_QUESTIONNAIRE = "Сначала пройдите анкету в разделе «📝 Анкета»."
    WORKOUTS_USE_MY_PLAN = (
        "План собирается персонально под вас.\n"
        "Откройте «📅 Мой план» в меню."
    )
    WORKOUTS_EXITED = "Возвращаю в главное меню."

    PLAN_NO_PLAN = (
        "Плана пока нет.\n"
        "Нажмите «🏋️ Тренировки» в меню — соберу персональную неделю."
    )
    PLAN_HEADER = "📅 Ваш план на неделю"
    TODAY_NO_WORKOUT = (
        "На сегодня тренировки нет — день восстановления 💪\n"
        "Завтра снова проверьте раздел «🏋️ На сегодня»."
    )
    TODAY_HEADER = "🏋️ Тренировка на сегодня"
    EXERCISE_NO_EXERCISE = "Упражнение не найдено."
    DONE_ALREADY = "Эта тренировка уже отмечена выполненной."
    DONE_OK = (
        "✅ Тренировка отмечена выполненной!\n"
        "Отличная работа — это помогает точнее подстраивать нагрузку."
    )
    WORKOUT_NOT_FOUND = "Тренировка не найдена."
    WORKOUT_NOT_YOURS = "Это не ваша тренировка."
    WORKOUT_REPLACE_UNAVAILABLE = "Не удалось подобрать замену для этого упражнения."
    WORKOUT_REPLACED = "Готово! Заменил упражнение: {old_name} → {new_name}"
    WORKOUT_DETAIL_HEADER = "🏋️ Тренировка"
    EFFORT_PROMPT = "Как по ощущениям от нагрузки?"
    EFFORT_SAVED = "Принято. Учту это в следующем плане."
    REFLECTION_PROMPT = "И коротко: как сейчас с энергией?"
    REFLECTION_SAVED = "Отлично, записал. Это поможет точнее подстроить следующую неделю."

    QUESTIONNAIRE_COMPLETED = "🎉 Анкета завершена!"
    QUESTIONNAIRE_FINISHED_PROMPT = "Анкета завершена. Что дальше?"
    QUESTIONNAIRE_LOAD_ERROR = "❌ Ошибка загрузки вопросов."
    QUESTIONNAIRE_UPDATED_RESTART = "Анкета обновилась. Запустите заново."
    QUESTIONNAIRE_SAVE_ERROR = "Не удалось сохранить ответ. Попробуйте еще раз."
    QUESTIONNAIRE_MULTI_INVALID = "Выберите вариант кнопкой или нажмите «✅ Готово»."
    QUESTIONNAIRE_MULTI_REQUIRED = "Выберите хотя бы один вариант."
    QUESTIONNAIRE_YES = "Да"
    QUESTIONNAIRE_NO = "Нет"
