from __future__ import annotations

from aiogram.fsm.context import FSMContext


class ResetStateMixin:
    @staticmethod
    async def _reset_state(state: FSMContext) -> None:
        await state.clear()
