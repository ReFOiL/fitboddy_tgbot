from __future__ import annotations

import re
from enum import StrEnum
from typing import Protocol


# Код plan-service: 4–16 символов, перед проверкой его приводят к верхнему регистру.
_CODE_RE = re.compile(r"^[A-Z0-9]{4,16}$")


class TelegramLinkResult(StrEnum):
    LINKED = "linked"
    INVALID_OR_EXPIRED = "invalid_or_expired"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"
    PRIVATE_ONLY = "private_only"


class TelegramLinkGateway(Protocol):
    async def confirm(self, code: str, chat_id: int) -> TelegramLinkResult:
        """Подтверждает уже нормализованный код."""


class TelegramLinkService:
    def __init__(self, gateway: TelegramLinkGateway) -> None:
        self._gateway = gateway

    async def confirm(self, *, code: str, chat_id: int) -> TelegramLinkResult:
        # plan-service принимает только положительный chat_id: личный чат, не группа.
        if chat_id <= 0:
            return TelegramLinkResult.PRIVATE_ONLY
        normalized = _normalize_code(code)
        if normalized is None:
            return TelegramLinkResult.INVALID_OR_EXPIRED
        return await self._gateway.confirm(normalized, chat_id)


def _normalize_code(raw: str) -> str | None:
    stripped = raw.strip()
    if not stripped:
        return None
    token = stripped.split(maxsplit=1)[0].upper()
    if _CODE_RE.fullmatch(token) is None:
        return None
    return token
