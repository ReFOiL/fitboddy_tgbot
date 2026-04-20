from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.user_plan_service import UserPlanService
from src.application.use_cases.workout.query.errors import WorkoutQueryPlanNotFound
from src.application.use_cases.workout.query.models import MyPlanViewData
from src.application.use_cases.workout.query.user_resolver import WorkoutTelegramUserResolver


class GetMyPlanUseCase:
    def __init__(self, uow: UnitOfWork, user_plan_service: UserPlanService) -> None:
        self._user_plan_service = user_plan_service
        self._user_resolver = WorkoutTelegramUserResolver(uow)

    async def get_plan(self, tg_user_id: int) -> MyPlanViewData:
        user = await self._user_resolver.resolve_user(tg_user_id)
        plan = await self._user_plan_service.get_or_create_plan(user.id)
        if plan is None:
            raise WorkoutQueryPlanNotFound()
        return MyPlanViewData(user_id=user.id, telegram_id=tg_user_id, plan=plan)
