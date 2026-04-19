from __future__ import annotations

from dataclasses import dataclass

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.presentation.web_admin.admin_jwt import AdminTokenPayload, decode_admin_access_token
from src.shared.config.settings import get_settings

logger = structlog.get_logger()

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AdminPrincipal:
    username: str
    is_superuser: bool


def admin_principal_from_payload(payload: AdminTokenPayload) -> AdminPrincipal:
    return AdminPrincipal(username=payload.username, is_superuser=payload.is_superuser)


def decode_bearer_token(token: str) -> AdminPrincipal:
    try:
        payload = decode_admin_access_token(get_settings(), token)
    except jwt.PyJWTError as e:
        logger.warning("admin.jwt.invalid", error=str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token") from e
    except ValueError as e:
        logger.warning("admin.jwt.config", error=str(e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin auth is not configured") from e
    return admin_principal_from_payload(payload)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AdminPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        logger.warning("admin.auth.missing_bearer")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing Bearer token")
    return decode_bearer_token(credentials.credentials)


async def require_superuser(principal: AdminPrincipal = Depends(get_current_admin)) -> AdminPrincipal:
    if not principal.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the bootstrap superuser can manage admin accounts",
        )
    return principal
