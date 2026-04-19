"""Правила CRYPTBOT при включённой оплате (без загрузки .env)."""
from __future__ import annotations

from typing import NamedTuple

import pytest

from src.shared.config.settings import AppSettings, CryptoBotSettings


class _CryptobotErrorCase(NamedTuple):
    payment_on: bool
    api_token: str
    webhook_secret: str
    match: str


class _CryptobotOkCase(NamedTuple):
    payment_on: bool
    api_token: str
    webhook_secret: str


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            _CryptobotErrorCase(True, "   ", "secret", "CRYPTBOT_API_TOKEN"),
            id="empty-token",
        ),
        pytest.param(
            _CryptobotErrorCase(True, "tok", "  ", "CRYPTBOT_WEBHOOK_SECRET"),
            id="empty-secret",
        ),
    ],
)
def test_validate_cryptobot_requirements_raises(case: _CryptobotErrorCase) -> None:
    cb = CryptoBotSettings.model_construct(api_token=case.api_token, webhook_secret=case.webhook_secret)
    with pytest.raises(ValueError, match=case.match):
        AppSettings.validate_cryptobot_requirements(case.payment_on, cb)


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(_CryptobotOkCase(True, "tok", "sec"), id="ok-when-payment-on"),
        pytest.param(_CryptobotOkCase(False, "", ""), id="ok-when-payment-off-empty"),
    ],
)
def test_validate_cryptobot_requirements_ok(case: _CryptobotOkCase) -> None:
    cb = CryptoBotSettings.model_construct(api_token=case.api_token, webhook_secret=case.webhook_secret)
    AppSettings.validate_cryptobot_requirements(case.payment_on, cb)
