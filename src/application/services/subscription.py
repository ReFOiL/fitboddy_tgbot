from __future__ import annotations

from datetime import datetime, timedelta

from src.domain.entities.user import Tariff, User


class SubscriptionService:
    def extend(self, user: User, days: int) -> None:
        now = datetime.utcnow()
        base = user.subscription_ends_at or now
        user.subscription_ends_at = max(base, now) + timedelta(days=days)
        user.tariff = Tariff.PREMIUM

