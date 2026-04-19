from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # Индекс для поиска платежей пользователя
    invoice_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        index=True,  # Индекс для фильтрации по статусу
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)  # Индекс для сортировки по дате

    __table_args__ = (
        # Составной индекс для частых запросов: платежи пользователя по статусу
        Index("idx_payment_user_status", "user_id", "status"),
        # CHECK: amount > 0
        CheckConstraint(
            "amount > 0",
            name="ck_payment_amount_positive",
        ),
    )

    user: Mapped[User] = relationship()


from src.domain.entities.user import User  # noqa: E402  # isort:skip

