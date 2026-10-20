import hmac
from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # Пустая строка допустима: рабочий токен может прийти из TELEGRAM_BOT_TOKEN.
    token: str = Field(default="", description="Устаревшее имя токена бота (BOT_TOKEN).")


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    url: str = Field(..., alias="DATABASE_URL")


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    url: str = Field(..., alias="REDIS_URL")


class CryptoBotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CRYPTBOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    api_token: str = Field(default="", alias="CRYPTBOT_API_TOKEN")
    webhook_secret: str = Field(default="", alias="CRYPTBOT_WEBHOOK_SECRET")


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    endpoint: str = Field(..., description="Internal endpoint for backend (e.g. minio:9000)")
    public_endpoint: str | None = Field(
        default=None,
        description="Public endpoint for presigned URLs (reachable from browser), e.g. localhost:9000",
    )
    secure: bool = False
    access_key: str = Field(..., alias="MINIO_ROOT_USER")
    secret_key: str = Field(..., alias="MINIO_ROOT_PASSWORD")
    bucket: str = "fitboddy"


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    otel_exporter_otlp_endpoint: str = Field(
        "http://tempo:4318/v1/traces",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )
    service_name: str = Field("fitboddy-bot", alias="SERVICE_NAME")


class PlanServiceSettings(BaseSettings):
    """plan-service: подтверждение привязки Telegram для уведомлений о тренировках."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    url: str = Field(
        default="",
        alias="PLAN_SERVICE_URL",
        description="Происхождение plan-service без пути, например http://plan-service:8000.",
    )
    internal_service_token: str = Field(
        default="",
        alias="INTERNAL_SERVICE_TOKEN",
        description="Тот же секрет, что INTERNAL_SERVICE_TOKEN у plan-service.",
    )


def _bot_settings() -> BotSettings:
    return BotSettings()


def _database_settings() -> DatabaseSettings:
    # Обязательные поля приходят из окружения; mypy источники pydantic-settings не видит.
    return DatabaseSettings()  # type: ignore[call-arg]


def _redis_settings() -> RedisSettings:
    return RedisSettings()  # type: ignore[call-arg]


def _cryptobot_settings() -> CryptoBotSettings:
    return CryptoBotSettings()


def _minio_settings() -> MinioSettings:
    return MinioSettings()  # type: ignore[call-arg]


def _observability_settings() -> ObservabilitySettings:
    return ObservabilitySettings()  # type: ignore[call-arg]


def _plan_service_settings() -> PlanServiceSettings:
    return PlanServiceSettings()


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    feature_payment_enabled: bool = Field(
        default=True,
        alias="FEATURE_PAYMENT_ENABLED",
        description="Если false — оплата выключена: CRYPTBOT_* не обязательны, доступ как у PREMIUM для всех.",
    )
    admin_bootstrap_username: str = Field(
        default="admin",
        alias="ADMIN_BOOTSTRAP_USERNAME",
        description="Логин первого суперпользователя (создаётся при пустой таблице admin_accounts).",
    )
    admin_bootstrap_password: str = Field(
        default="",
        alias="ADMIN_BOOTSTRAP_PASSWORD",
        description="Пароль первого суперпользователя; пусто — запись не создаётся (таблица остаётся пустой).",
    )
    admin_jwt_secret: str = Field(
        default="",
        alias="ADMIN_JWT_SECRET",
        description="Секрет HS256 для JWT админки; обязателен для входа.",
    )
    admin_jwt_expire_minutes: int = Field(
        default=480,
        alias="ADMIN_JWT_EXPIRE_MINUTES",
        ge=5,
        le=10080,
        description="Срок жизни access-токена админки (минуты).",
    )
    # Фабрики, а не готовые экземпляры: иначе вложенные настройки читают окружение при импорте.
    telegram_bot_token: str = Field(
        default="",
        alias="TELEGRAM_BOT_TOKEN",
        description="Токен бота, общий с воркером уведомлений plan-service.",
    )
    bot: BotSettings = Field(default_factory=_bot_settings)
    database: DatabaseSettings = Field(default_factory=_database_settings)
    redis: RedisSettings = Field(default_factory=_redis_settings)
    cryptobot: CryptoBotSettings = Field(default_factory=_cryptobot_settings)
    minio: MinioSettings = Field(default_factory=_minio_settings)
    observability: ObservabilitySettings = Field(default_factory=_observability_settings)
    plan_service: PlanServiceSettings = Field(default_factory=_plan_service_settings)

    @staticmethod
    def validate_cryptobot_requirements(
        feature_payment_enabled: bool,
        cryptobot: CryptoBotSettings,
    ) -> None:
        """Правила CRYPTBOT при включённой оплате (удобно тестировать без .env)."""
        if feature_payment_enabled:
            if not cryptobot.api_token.strip():
                raise ValueError(
                    "Задайте CRYPTBOT_API_TOKEN или отключите оплату: FEATURE_PAYMENT_ENABLED=false",
                )
            if not cryptobot.webhook_secret.strip():
                raise ValueError(
                    "Задайте CRYPTBOT_WEBHOOK_SECRET или отключите оплату: FEATURE_PAYMENT_ENABLED=false",
                )

    @staticmethod
    def resolve_telegram_bot_token(telegram_bot_token: str, legacy_bot_token: str) -> str:
        """Один токен у этого бота и у воркера уведомлений plan-service.

        TELEGRAM_BOT_TOKEN — основное имя. BOT_TOKEN остаётся, чтобы уже
        настроенная оплата не требовала переименования переменной.
        """
        explicit = telegram_bot_token.strip()
        legacy = legacy_bot_token.strip()
        if explicit and legacy and not _same_secret(explicit, legacy):
            raise ValueError(
                "TELEGRAM_BOT_TOKEN и BOT_TOKEN различаются. "
                "Нужен один токен — тот же, что у воркера уведомлений.",
            )
        token = explicit or legacy
        if not token:
            raise ValueError(
                "Задайте TELEGRAM_BOT_TOKEN (тот же, что у воркера уведомлений). "
                "BOT_TOKEN по-прежнему принимается, если нового имени нет.",
            )
        return token

    @model_validator(mode="after")
    def _require_cryptobot_when_payments_on(self) -> Self:
        self.validate_cryptobot_requirements(self.feature_payment_enabled, self.cryptobot)
        resolved = self.resolve_telegram_bot_token(self.telegram_bot_token, self.bot.token)
        if self.bot.token != resolved:
            # DI бота читает bot.token: и оплата, и уведомления уходят тем же ботом.
            self.bot = self.bot.model_copy(update={"token": resolved})
        return self


def _same_secret(left: str, right: str) -> bool:
    if len(left) != len(right):
        return False
    return hmac.compare_digest(left, right)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

