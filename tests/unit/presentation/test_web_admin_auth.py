"""JWT и пароли для админ API."""
from __future__ import annotations

from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException

from src.commons.passwords import hash_password, verify_password
from src.presentation.web_admin.admin_jwt import AdminTokenPayload, create_admin_access_token, decode_admin_access_token
from src.presentation.web_admin.auth import decode_bearer_token
from src.shared.config.settings import AppSettings, BotSettings, CryptoBotSettings, DatabaseSettings, MinioSettings, ObservabilitySettings, RedisSettings


def _jwt_settings(*, admin_jwt_secret: str = "unit-test-jwt-secret-min-32-bytes-long!!") -> AppSettings:
    return AppSettings.model_construct(
        feature_payment_enabled=False,
        admin_bootstrap_username="admin",
        admin_bootstrap_password="",
        admin_jwt_secret=admin_jwt_secret,
        admin_jwt_expire_minutes=60,
        bot=BotSettings.model_construct(token="t"),
        database=DatabaseSettings.model_construct(url="postgresql+asyncpg://u:p@localhost/db"),
        redis=RedisSettings.model_construct(url="redis://localhost:6379/0"),
        cryptobot=CryptoBotSettings.model_construct(api_token="", webhook_secret=""),
        minio=MinioSettings.model_construct(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="s",
        ),
        observability=ObservabilitySettings.model_construct(),
    )


def test_password_hash_roundtrip() -> None:
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip() -> None:
    s = _jwt_settings()
    token = create_admin_access_token(s, username="admin", is_superuser=True)
    out = decode_admin_access_token(s, token)
    assert out == AdminTokenPayload(username="admin", is_superuser=True)


def test_decode_bearer_token_ok() -> None:
    s = _jwt_settings()
    token = create_admin_access_token(s, username="u", is_superuser=False)
    with patch("src.presentation.web_admin.auth.get_settings", return_value=s):
        p = decode_bearer_token(token)
    assert p.username == "u"
    assert p.is_superuser is False


def test_decode_bearer_token_invalid() -> None:
    s = _jwt_settings()
    with patch("src.presentation.web_admin.auth.get_settings", return_value=s):
        with pytest.raises(HTTPException) as exc:
            decode_bearer_token("not-a-jwt")
        assert exc.value.status_code == 403


def test_jwt_requires_secret() -> None:
    s = _jwt_settings(admin_jwt_secret="")
    with pytest.raises(ValueError):
        create_admin_access_token(s, username="a", is_superuser=True)
