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
    token: str = Field(..., description="Telegram bot token")


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
    bot: BotSettings = BotSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    cryptobot: CryptoBotSettings = CryptoBotSettings()
    minio: MinioSettings = MinioSettings()
    observability: ObservabilitySettings = ObservabilitySettings()

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

    @model_validator(mode="after")
    def _require_cryptobot_when_payments_on(self) -> Self:
        self.validate_cryptobot_requirements(self.feature_payment_enabled, self.cryptobot)
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

