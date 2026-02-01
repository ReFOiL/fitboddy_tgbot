from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserRegistered:
    user_id: int
    occurred_at: datetime

