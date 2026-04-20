from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.plan_management import UserPlanOrchestrator
from src.domain.entities.training_plan import TrainingPlan


class UserPlanService:
    def __init__(
        self,
        uow: UnitOfWork,
        orchestrator: UserPlanOrchestrator,
    ) -> None:
        self._uow = uow
        self._orchestrator = orchestrator

    async def get_or_create_plan(self, user_id: int) -> TrainingPlan | None:
        return await self._orchestrator.get_or_create_active_plan(self._uow, user_id)
