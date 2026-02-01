from __future__ import annotations

from typing import Protocol


class PaymentInvoice(Protocol):
    id: str
    pay_url: str


class IPaymentGateway(Protocol):
    async def create_invoice(self, user_id: int, amount: float) -> PaymentInvoice: ...
    async def verify_webhook(self, body: bytes, signature: str) -> bool: ...

