from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.domain.entities.user import Tariff, User
from src.shared.config.settings import AppSettings


class SubscriptionService:
    def extend(self, user: User, days: int) -> None:
        now = datetime.utcnow()
        base = user.subscription_ends_at or now
        user.subscription_ends_at = max(base, now) + timedelta(days=days)
        user.tariff = Tariff.PREMIUM


@dataclass(slots=True)
class PremiumAccess:
    """
    Единая точка: есть ли у пользователя доступ платных функций.

    При ``FEATURE_PAYMENT_ENABLED=false`` в настройках — у всех доступ как у оплативших
    (без проверки тарифа и даты подписки).
    """

    _settings: AppSettings

    def user_has_premium_access(self, user: User, *, now: datetime | None = None) -> bool:
        if not self._settings.feature_payment_enabled:
            return True
        if user.tariff != Tariff.PREMIUM:
            return False
        ends = user.subscription_ends_at
        if ends is None:
            return False
        current = now or datetime.now(UTC)
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        return ends >= current

