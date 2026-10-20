from __future__ import annotations

import httpx
import structlog

from src.application.services.telegram_link import TelegramLinkResult


logger = structlog.get_logger()

# Внутренний маршрут plan-service. Отвязки с X-Service-Token нет:
# DELETE /api/v1/plans/me/notifications/telegram ждёт Bearer пользователя.
_CONFIRM_PATH = "/api/v1/plans/internal/notifications/telegram"
_SERVICE_TOKEN_HEADER = "X-Service-Token"


class PlanTelegramLinkClient:
    """POST кода и chat_id в plan-service.

    Токен бота сюда не входит: и этот процесс, и воркер уведомлений
    ходят в Telegram с одним TELEGRAM_BOT_TOKEN, а здесь только chat_id.
    """

    def __init__(
        self,
        base_url: str,
        service_token: str,
        *,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._service_token = service_token.strip()
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def confirm(self, code: str, chat_id: int) -> TelegramLinkResult:
        if not self._base_url or not self._service_token:
            # Пустой токен plan-service отвергает. Не шлём запрос и не пишем секрет в лог.
            logger.warning("telegram_link.not_configured")
            return TelegramLinkResult.NOT_CONFIGURED
        # Один запрос без повтора: если код уже сожжён, а ответ потерялся,
        # повтор выглядел бы как «код неверный», хотя чат уже привязан.
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                # MockTransport в тестах синхронный; AsyncClient его принимает.
                transport=self._transport,  # type: ignore[arg-type]
            ) as client:
                response = await client.post(
                    f"{self._base_url}{_CONFIRM_PATH}",
                    json={"code": code, "chat_id": chat_id},
                    headers={_SERVICE_TOKEN_HEADER: self._service_token},
                )
        except httpx.HTTPError as exc:
            logger.warning("telegram_link.transport_error", error_type=type(exc).__name__)
            return TelegramLinkResult.UNAVAILABLE
        return _result_from_response(response)


def _result_from_response(response: httpx.Response) -> TelegramLinkResult:
    if response.status_code == 200:
        try:
            payload = response.json()
        except ValueError:
            logger.warning("telegram_link.bad_body", status_code=response.status_code)
            return TelegramLinkResult.UNAVAILABLE
        if isinstance(payload, dict) and payload.get("telegram_linked") is True:
            return TelegramLinkResult.LINKED
        logger.warning("telegram_link.unexpected_body", status_code=response.status_code)
        return TelegramLinkResult.UNAVAILABLE
    # 404 — код не найден, использован или истёк. 422 — форма не прошла проверку.
    if response.status_code in {404, 422}:
        return TelegramLinkResult.INVALID_OR_EXPIRED
    logger.warning("telegram_link.http_error", status_code=response.status_code)
    return TelegramLinkResult.UNAVAILABLE
