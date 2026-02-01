from __future__ import annotations

from src.application.services.questionnaire_flow_queries import QuestionnaireFlowQueries
from src.presentation.telegram_bot.flows.questionnaire.state_service import QuestionnaireStateService


class QuestionNavigation:
    def __init__(
        self,
        queries: QuestionnaireFlowQueries,
        state: QuestionnaireStateService,
    ) -> None:
        self._queries = queries
        self._state = state

    async def ordered_keys(self) -> list[str]:
        cached = await self._state.get_ordered_keys()
        if cached is not None:
            return cached
        ordered = await self._queries.ordered_keys()
        await self._state.set_ordered_keys(ordered)
        return ordered

    async def prev_key(self, current_key: str) -> str | None:
        keys = await self.ordered_keys()
        if current_key not in keys:
            return None
        idx = keys.index(current_key)
        if idx <= 0:
            return None
        return keys[idx - 1]

    async def has_prev(self, current_key: str) -> bool:
        return await self.prev_key(current_key) is not None
