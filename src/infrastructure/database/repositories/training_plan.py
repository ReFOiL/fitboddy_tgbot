from __future__ import annotations

from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.application.interfaces.repositories import ITrainingPlanRepository
from src.domain.entities.training_plan import (
    ScheduledWorkout,
    ScheduledWorkoutExercise,
    TrainingPlan,
    TrainingPlanStatus,
)
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
                selectinload(TrainingPlan.scheduled_workouts)
                .selectinload(ScheduledWorkout.session_exercises)
                .selectinload(ScheduledWorkoutExercise.exercise),
            )
            .order_by(TrainingPlan.start_date.desc())
            .limit(1)
        )
        return result.scalars().one_or_none()

    async def archive_active_for_user(self, user_id: int) -> None:
        await self._session.execute(
            update(TrainingPlan)
            .where(
                TrainingPlan.user_id == user_id,
                TrainingPlan.status == TrainingPlanStatus.ACTIVE,
            )
            .values(status=TrainingPlanStatus.ARCHIVED)
        )

    async def get_by_id(self, plan_id: int) -> TrainingPlan | None:
        result = await self._session.execute(
            select(TrainingPlan)
            .where(TrainingPlan.id == plan_id)
            .options(
                selectinload(TrainingPlan.scheduled_workouts)
                .selectinload(ScheduledWorkout.session_exercises)
                .selectinload(ScheduledWorkoutExercise.exercise),
            )
        )
        return result.scalars().one_or_none()

    async def list_for_user(self, user_id: int, *, limit: int = 30) -> list[TrainingPlan]:
        result = await self._session.execute(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == user_id)
            .order_by(TrainingPlan.start_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
