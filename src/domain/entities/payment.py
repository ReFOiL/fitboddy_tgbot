from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import Enum, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invoice_id: Mapped[str] = mapped_column(String(128), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship()


from src.domain.entities.user import User  # noqa: E402  # isort:skip

