from sqlalchemy import select

from src.application.interfaces.repositories import IPaymentRepository
from src.domain.entities.payment import Payment
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class PaymentRepository(SQLAlchemyRepository, IPaymentRepository):
    async def add(self, payment: Payment) -> None:
        self._session.add(payment)

    async def get_by_invoice_id(self, invoice_id: str) -> Payment | None:
        result = await self._session.execute(select(Payment).where(Payment.invoice_id == invoice_id))
        return result.scalar_one_or_none()

