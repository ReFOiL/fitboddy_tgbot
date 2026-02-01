from __future__ import annotations

from typing import Protocol


class INotifier(Protocol):
    async def send_message(self, user_id: int, text: str) -> None: ...


class NotificationService:
    def __init__(self, notifier: INotifier) -> None:
        self._notifier = notifier

    async def payment_success(self, user_id: int) -> None:
        await self._notifier.send_message(user_id, "Оплата получена. Спасибо!")

