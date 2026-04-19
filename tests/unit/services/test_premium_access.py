"""Доступ Premium при включённой/выключенной оплате."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TypedDict

import pytest

from src.application.services.subscription import PremiumAccess
from src.domain.entities.user import Tariff, User
from src.shared.config.settings import AppSettings


def _user(
    *,
    tariff: Tariff = Tariff.FREE,
    subscription_ends_at: datetime | None = None,
) -> User:
    return User(
        telegram_id=42,
        username="t",
        tariff=tariff,
        subscription_ends_at=subscription_ends_at,
    )


def _ends_utc(*, days_offset: int) -> datetime:
    return datetime.now(UTC) + timedelta(days=days_offset)


def _ends_naive(*, days_offset: int) -> datetime:
    return _ends_utc(days_offset=days_offset).replace(tzinfo=None)


class _PremiumAccessCallKwargs(TypedDict, total=False):
    now: datetime


@pytest.mark.parametrize(
    ("payment_on", "user", "expected", "call_kwargs"),
    [
        pytest.param(False, _user(), True, {}, id="payment-off-free-anyone"),
        pytest.param(False, _user(tariff=Tariff.PREMIUM), True, {}, id="payment-off-premium"),
        pytest.param(True, _user(tariff=Tariff.FREE), False, {}, id="payment-on-free"),
        pytest.param(
            True,
            _user(tariff=Tariff.PREMIUM, subscription_ends_at=_ends_utc(days_offset=5)),
            True,
            {},
            id="payment-on-premium-active",
        ),
        pytest.param(
            True,
            _user(tariff=Tariff.PREMIUM, subscription_ends_at=_ends_utc(days_offset=-1)),
            False,
            {},
            id="payment-on-premium-expired",
        ),
        pytest.param(
            True,
            _user(tariff=Tariff.PREMIUM, subscription_ends_at=None),
            False,
            {},
            id="payment-on-premium-no-end",
        ),
        pytest.param(
            True,
            _user(tariff=Tariff.PREMIUM, subscription_ends_at=_ends_naive(days_offset=1)),
            True,
            {"now": datetime.now(UTC)},
            id="payment-on-premium-naive-end-normalized",
        ),
    ],
)
def test_user_has_premium_access(
    payment_on: bool,
    user: User,
    expected: bool,
    call_kwargs: _PremiumAccessCallKwargs,
) -> None:
    settings = AppSettings.model_construct(feature_payment_enabled=payment_on)
    pa = PremiumAccess(_settings=settings)
    assert pa.user_has_premium_access(user, **call_kwargs) is expected
