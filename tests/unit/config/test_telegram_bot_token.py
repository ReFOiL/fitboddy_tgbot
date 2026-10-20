"""Токен бота общий с воркером уведомлений, оплата при этом не отключается."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.config.settings import AppSettings


def _prepare_env(monkeypatch: pytest.MonkeyPatch, **extra: str) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("FEATURE_PAYMENT_ENABLED", "false")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ROOT_USER", "minio")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "secret")
    for name in ("BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "PLAN_SERVICE_URL", "INTERNAL_SERVICE_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    for key, value in extra.items():
        monkeypatch.setenv(key, value)


def test_resolve_telegram_bot_token_prefers_shared_name() -> None:
    assert AppSettings.resolve_telegram_bot_token(" worker ", "worker") == "worker"


def test_resolve_telegram_bot_token_keeps_legacy_name() -> None:
    assert AppSettings.resolve_telegram_bot_token("  ", "legacy") == "legacy"


def test_resolve_telegram_bot_token_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        AppSettings.resolve_telegram_bot_token("worker", "legacy")


def test_resolve_telegram_bot_token_requires_one_value() -> None:
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        AppSettings.resolve_telegram_bot_token("", "")


def test_settings_copy_shared_token_onto_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_env(monkeypatch, TELEGRAM_BOT_TOKEN="worker-token")
    settings = AppSettings()
    assert settings.bot.token == "worker-token"
    assert settings.plan_service.url == ""
    assert settings.plan_service.internal_service_token == ""


def test_settings_keep_legacy_bot_token(monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_env(monkeypatch, BOT_TOKEN="legacy-token", PLAN_SERVICE_URL="http://plan.test", INTERNAL_SERVICE_TOKEN="svc")
    settings = AppSettings()
    assert settings.bot.token == "legacy-token"
    assert settings.telegram_bot_token == ""
    assert settings.plan_service.url == "http://plan.test"
    assert settings.plan_service.internal_service_token == "svc"


def test_settings_reject_different_bot_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_env(monkeypatch, TELEGRAM_BOT_TOKEN="worker-token", BOT_TOKEN="legacy-token")
    with pytest.raises(ValidationError, match="TELEGRAM_BOT_TOKEN"):
        AppSettings()


def test_payment_still_requires_cryptobot_when_bot_token_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_env(monkeypatch, BOT_TOKEN="legacy-token", FEATURE_PAYMENT_ENABLED="true")
    with pytest.raises(ValidationError, match="CRYPTBOT_API_TOKEN"):
        AppSettings()
