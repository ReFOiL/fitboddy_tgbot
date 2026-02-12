from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import ITrainingPlanRepository
from src.domain.entities.training_plan import ScheduledWorkout, TrainingPlan, TrainingPlanStatus
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class TrainingPlanRepository(SQLAlchemyRepository, ITrainingPlanRepository):
    async def add(self, plan: TrainingPlan) -> None:
        self._session.add(plan)

    async def get_active_for_user(self, user_id: int) -> TrainingPlan | None:
        result = await self._session.execute(
            select(TrainingPlan)
            .where(
                TrainingPlan.user_id == user_id,
                TrainingPlan.status == TrainingPlanStatus.ACTIVE,
            )
            .options(
                selectinload(TrainingPlan.scheduled_workouts).selectinload(ScheduledWorkout.template)
            )
            .order_by(TrainingPlan.start_date.desc())
            .limit(1)
        )
        return result.scalars().one_or_none()
