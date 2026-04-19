"""CryptoBot use case: создание инвойса при выключенной оплате."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest

from src.application.services.notification import NotificationService
from src.application.services.subscription import SubscriptionService
from src.application.use_cases.payment.cryptobot import CryptoBotPaymentUseCase
from src.shared.config.settings import AppSettings


@pytest.mark.asyncio
async def test_create_invoice_raises_when_payment_feature_disabled() -> None:
    settings = create_autospec(AppSettings, instance=True)
    settings.feature_payment_enabled = False
    with patch("src.application.use_cases.payment.cryptobot.get_settings", return_value=settings):
        uc = CryptoBotPaymentUseCase(
            gateway=AsyncMock(),
            uow=MagicMock(),
            subscription_service=SubscriptionService(),
            notification_service=MagicMock(spec=NotificationService),
        )
        with pytest.raises(RuntimeError, match="Оплата отключена"):
            await uc.create_invoice(user_id=1, amount=10.0)
