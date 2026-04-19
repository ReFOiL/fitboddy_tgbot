from __future__ import annotations

from src.application.interfaces.payment_gateway import IPaymentGateway
from src.application.interfaces.repositories import UnitOfWork
from src.application.services.notification import NotificationService
from src.application.services.subscription import SubscriptionService
from src.domain.entities.payment import Payment, PaymentStatus
from src.shared.config.settings import get_settings


class CryptoBotPaymentUseCase:
    def __init__(
        self,
        gateway: IPaymentGateway,
        uow: UnitOfWork,
        subscription_service: SubscriptionService,
        notification_service: NotificationService,
    ) -> None:
        self._gateway = gateway
        self._uow = uow
        self._subscription = subscription_service
        self._notifications = notification_service

    async def create_invoice(self, user_id: int, amount: float) -> str:
        if not get_settings().feature_payment_enabled:
            raise RuntimeError("Оплата отключена (FEATURE_PAYMENT_ENABLED=false).")
        invoice = await self._gateway.create_invoice(user_id=user_id, amount=amount)
        async with self._uow:
            payment = Payment(user_id=user_id, invoice_id=invoice.id, amount=amount)
            await self._uow.payments.add(payment)
            await self._uow.commit()
        return invoice.pay_url

    async def handle_success(self, invoice_id: str, days: int) -> None:
        user_id: int | None = None
        async with self._uow:
            payment = await self._uow.payments.get_by_invoice_id(invoice_id)
            if not payment:
                return
            payment.status = PaymentStatus.PAID
            user_id = payment.user_id
            user = await self._uow.users.get_by_id(payment.user_id)
            if user:
                self._subscription.extend(user, days=days)
            await self._uow.commit()
        if user_id is not None:
            await self._notifications.payment_success(user_id)

