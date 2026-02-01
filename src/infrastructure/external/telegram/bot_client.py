from aiogram import Bot

from src.application.services.notification import INotifier


class TelegramNotifier(INotifier):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send_message(self, user_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=user_id, text=text)

