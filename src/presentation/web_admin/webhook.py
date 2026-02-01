from fastapi import APIRouter, Depends, Header, Request
from dependency_injector.wiring import Provide, inject

from src.application.use_cases.payment.cryptobot import CryptoBotPaymentUseCase
from src.infrastructure.external.cryptobot.client import CryptoBotClient
from src.shared.di.containers import Container


router = APIRouter()


@router.post("/cryptobot")
@inject
async def cryptobot_webhook(
    request: Request,
    signature: str | None = Header(default=None, alias="crypto-pay-api-signature"),
    payment_use_case: CryptoBotPaymentUseCase = Depends(Provide[Container.payment_use_case]),
    client: CryptoBotClient = Depends(Provide[Container.cryptobot_client]),
) -> dict:
    body = await request.body()
    if not signature or not await client.verify_webhook(body, signature):
        return {"ok": False}
    payload = await request.json()
    invoice_id = str(payload.get("invoice_id", ""))
    status = payload.get("status")
    if status == "paid" and invoice_id:
        await payment_use_case.handle_success(invoice_id=invoice_id, days=30)
    return {"ok": True}

