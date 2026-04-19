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

