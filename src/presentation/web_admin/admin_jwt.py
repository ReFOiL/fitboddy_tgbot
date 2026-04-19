"""JWT доступа к админ API (HS256)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import jwt

from src.shared.config.settings import AppSettings


@dataclass(frozen=True)
class AdminTokenPayload:
    username: str
    is_superuser: bool


def create_admin_access_token(settings: AppSettings, *, username: str, is_superuser: bool) -> str:
    if not settings.admin_jwt_secret.strip():
        raise ValueError("ADMIN_JWT_SECRET is not set")
    now = datetime.now(tz=UTC)
    exp = now + timedelta(minutes=settings.admin_jwt_expire_minutes)
    payload: dict[str, str | bool | datetime] = {
        "sub": username,
        "super": is_superuser,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm="HS256")


def decode_admin_access_token(settings: AppSettings, token: str) -> AdminTokenPayload:
    if not settings.admin_jwt_secret.strip():
        raise jwt.InvalidTokenError("ADMIN_JWT_SECRET is not set")
    data = jwt.decode(
        token,
        settings.admin_jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )
    username = data["sub"]
    if not isinstance(username, str) or not username:
        raise jwt.InvalidTokenError("invalid sub")
    is_super = bool(data.get("super", False))
    return AdminTokenPayload(username=username, is_superuser=is_super)
