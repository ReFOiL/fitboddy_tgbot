from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PaymentReceived:
    user_id: int
    invoice_id: str
    amount: float
    occurred_at: datetime

