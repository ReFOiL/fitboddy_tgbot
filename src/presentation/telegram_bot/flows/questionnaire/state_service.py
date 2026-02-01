from __future__ import annotations

from aiogram.fsm.context import FSMContext


class QuestionnaireStateService:
    _CURRENT_KEY = "current_question_key"
    _ORDERED_KEYS = "ordered_question_keys"
    _USER_DB_ID = "user_db_id"

    def __init__(self, state: FSMContext) -> None:
        self._state = state

    async def clear(self) -> None:
        await self._state.clear()

    async def set_current_key(self, key: str) -> None:
        await self._state.update_data(current_question_key=key)

    async def get_current_key(self) -> str | None:
        data = await self._state.get_data()
        raw = data.get(self._CURRENT_KEY)
        return str(raw) if raw else None

    async def set_ordered_keys(self, keys: list[str]) -> None:
        await self._state.update_data(ordered_question_keys=keys)

    async def get_ordered_keys(self) -> list[str] | None:
        data = await self._state.get_data()
        raw = data.get(self._ORDERED_KEYS)
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            return raw
        return None

    async def set_user_db_id(self, user_id: int) -> None:
        await self._state.update_data(user_db_id=user_id)

    async def get_user_db_id(self) -> int | None:
        data = await self._state.get_data()
        raw = data.get(self._USER_DB_ID)
        return int(raw) if isinstance(raw, int) else None
