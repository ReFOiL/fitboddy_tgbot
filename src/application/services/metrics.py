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
plan_generation_runs_total = Counter(
    "plan_generation_runs_total",
    "Количество генераций тренировочных планов",
    ["goal", "level", "phase", "is_first_plan"],
)
plan_adherence_score = Histogram(
    "plan_adherence_score",
    "Adherence score завершённого цикла",
    buckets=(0.0, 0.25, 0.5, 0.65, 0.8, 1.0),
)
plan_novelty_ratio = Histogram(
    "plan_novelty_ratio",
    "Доля новых упражнений относительно прошлого цикла",
    buckets=(0.0, 0.2, 0.35, 0.5, 0.65, 0.8, 1.0),
)
plan_cycle_completion_rate = Histogram(
    "plan_cycle_completion_rate",
    "Доля завершенных тренировок в цикле",
    buckets=(0.0, 0.25, 0.5, 0.65, 0.8, 1.0),
)
workout_retention_signal_total = Counter(
    "workout_retention_signal_total",
    "Сигналы вовлеченности для D7/D30 baseline",
    ["window"],
)
workout_nudges_total = Counter(
    "workout_nudges_total",
    "Количество отправленных smart nudges",
    ["kind"],
)
workout_reflections_total = Counter(
    "workout_reflections_total",
    "Ответы микро-рефлексии после тренировки",
    ["energy"],
)

