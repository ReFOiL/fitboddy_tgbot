"""Привязка чата: код, личный чат и контракт plan-service."""
from __future__ import annotations

import json

import httpx
import pytest

from src.application.services.telegram_link import TelegramLinkResult, TelegramLinkService
from src.infrastructure.external.plan_service.telegram_link_client import PlanTelegramLinkClient


class _Gateway:
    def __init__(self, result: TelegramLinkResult = TelegramLinkResult.LINKED) -> None:
        self.result = result
        self.calls: list[tuple[str, int]] = []

    async def confirm(self, code: str, chat_id: int) -> TelegramLinkResult:
        self.calls.append((code, chat_id))
        return self.result


@pytest.mark.asyncio
async def test_confirm_normalizes_code_and_calls_gateway() -> None:
    gateway = _Gateway()
    result = await TelegramLinkService(gateway).confirm(code=" abcd2345 extra", chat_id=42)
    assert result is TelegramLinkResult.LINKED
    assert gateway.calls == [("ABCD2345", 42)]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "chat_id", "expected"),
    [
        ("", 42, TelegramLinkResult.INVALID_OR_EXPIRED),
        ("abc", 42, TelegramLinkResult.INVALID_OR_EXPIRED),
        ("bad code!", 42, TelegramLinkResult.INVALID_OR_EXPIRED),
        ("ABCD2345", 0, TelegramLinkResult.PRIVATE_ONLY),
        ("ABCD2345", -100, TelegramLinkResult.PRIVATE_ONLY),
    ],
)
async def test_confirm_rejects_bad_input_without_gateway(
    code: str,
    chat_id: int,
    expected: TelegramLinkResult,
) -> None:
    gateway = _Gateway()
    result = await TelegramLinkService(gateway).confirm(code=code, chat_id=chat_id)
    assert result is expected
    assert gateway.calls == []


def _forbid_request(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"unexpected request {request.method} {request.url}")


@pytest.mark.asyncio
async def test_client_posts_code_and_chat_id_with_service_token() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["token"] = request.headers["X-Service-Token"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"telegram_linked": True})

    client = PlanTelegramLinkClient(
        base_url="http://plan.test/",
        service_token="svc-token",
        transport=httpx.MockTransport(handler),
    )
    result = await client.confirm("ABCD2345", 9001)
    assert result is TelegramLinkResult.LINKED
    assert seen["url"] == "http://plan.test/api/v1/plans/internal/notifications/telegram"
    assert seen["token"] == "svc-token"
    assert seen["body"] == {"code": "ABCD2345", "chat_id": 9001}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (404, {"detail": "link code is invalid or expired"}, TelegramLinkResult.INVALID_OR_EXPIRED),
        (422, {"detail": "invalid"}, TelegramLinkResult.INVALID_OR_EXPIRED),
        (401, {"detail": "invalid service token"}, TelegramLinkResult.UNAVAILABLE),
        (503, {"detail": "down"}, TelegramLinkResult.UNAVAILABLE),
        (200, {"telegram_linked": False}, TelegramLinkResult.UNAVAILABLE),
    ],
)
async def test_client_maps_plan_service_statuses(
    status: int,
    body: dict[str, object],
    expected: TelegramLinkResult,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body)

    client = PlanTelegramLinkClient("http://plan.test", "svc-token", transport=httpx.MockTransport(handler))
    assert await client.confirm("ABCD2345", 1) is expected


@pytest.mark.asyncio
async def test_client_treats_transport_errors_as_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client = PlanTelegramLinkClient("http://plan.test", "svc-token", transport=httpx.MockTransport(handler))
    assert await client.confirm("ABCD2345", 1) is TelegramLinkResult.UNAVAILABLE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("base_url", "token"),
    [
        ("", "svc-token"),
        ("http://plan.test", "  "),
    ],
)
async def test_client_skips_request_when_not_configured(base_url: str, token: str) -> None:
    client = PlanTelegramLinkClient(base_url, token, transport=httpx.MockTransport(_forbid_request))
    assert await client.confirm("ABCD2345", 1) is TelegramLinkResult.NOT_CONFIGURED
