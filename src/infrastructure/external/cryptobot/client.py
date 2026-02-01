from __future__ import annotations

import asyncio
import hmac
import hashlib
from dataclasses import dataclass

import httpx

from src.application.interfaces.payment_gateway import IPaymentGateway


@dataclass(slots=True)
class InvoiceResponse:
    id: str
    pay_url: str


class CryptoBotClient(IPaymentGateway):
    def __init__(
        self,
        api_token: str,
        webhook_secret: str,
        base_url: str = "https://pay.crypt.bot/api",
    ) -> None:
        self._api_token = api_token
        self._webhook_secret = webhook_secret
        self._base_url = base_url

    async def create_invoice(self, user_id: int, amount: float) -> InvoiceResponse:
        payload = {"asset": "USDT", "amount": amount, "description": f"Fitboddy subscription {user_id}"}
        data = await self._request("createInvoice", payload)
        return InvoiceResponse(id=str(data["invoice_id"]), pay_url=data["pay_url"])

    async def verify_webhook(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            self._webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def _request(self, method: str, payload: dict) -> dict:
        headers = {"Crypto-Pay-API-Token": self._api_token}
        retries = 3
        delay = 0.5
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            for attempt in range(retries):
                try:
                    response = await client.post(f"/{method}", json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    if not data.get("ok"):
                        raise httpx.HTTPError(f"CryptoBot error: {data}")
                    return data["result"]
                except (httpx.HTTPError, httpx.TimeoutException):
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2
        raise RuntimeError("CryptoBot request failed")

