from functools import lru_cache
from pydantic import Field
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
    api_token: str = Field(..., alias="CRYPTBOT_API_TOKEN")
    webhook_secret: str = Field(..., alias="CRYPTBOT_WEBHOOK_SECRET")


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
        extra="ignore",
    )
    bot: BotSettings = BotSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    cryptobot: CryptoBotSettings = CryptoBotSettings()
    minio: MinioSettings = MinioSettings()
    observability: ObservabilitySettings = ObservabilitySettings()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

