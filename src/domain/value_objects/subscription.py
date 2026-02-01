from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.user import Tariff

@dataclass(frozen=True, slots=True)
class Subscription:
    tariff: Tariff
    ends_at: datetime | None

