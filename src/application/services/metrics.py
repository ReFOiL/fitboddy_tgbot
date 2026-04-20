from __future__ import annotations

from prometheus_client import Counter, Histogram


bot_messages_total = Counter(
    "bot_messages_total",
    "Количество сообщений бота по командам",
    ["command"],
)
payments_successful_total = Counter(
    "payments_successful_total",
    "Успешные платежи",
)
user_registrations_total = Counter(
    "user_registrations_total",
    "Регистрации пользователей",
)
database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Время выполнения запросов БД",
)
workout_use_case_runs_total = Counter(
    "workout_use_case_runs_total",
    "Количество запусков workout use-cases",
    ["use_case"],
)
workout_use_case_failures_total = Counter(
    "workout_use_case_failures_total",
    "Количество ошибок workout use-cases",
    ["use_case"],
)
workout_use_case_duration_seconds = Histogram(
    "workout_use_case_duration_seconds",
    "Время выполнения workout use-cases",
    ["use_case"],
)
exercise_matching_runs_total = Counter(
    "exercise_matching_runs_total",
    "Количество запусков сопоставления упражнений",
)
exercise_matching_duration_seconds = Histogram(
    "exercise_matching_duration_seconds",
    "Время выполнения сопоставления упражнений",
)

