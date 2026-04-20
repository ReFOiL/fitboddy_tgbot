"""Админка: просмотр и правка планов тренировок пользователя."""
from __future__ import annotations

from datetime import date, datetime, timezone

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.training_plan import (
    ScheduledWorkout,
    ScheduledWorkoutExercise,
    TrainingPlan,
    TrainingPlanStatus,
)
from src.domain.value_objects.workout_profile import PerceivedEffort


class TrainingPlanAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_active_plan(self, user_id: int) -> TrainingPlan | None:
        async with self._uow:
            return await self._uow.training_plans.get_active_for_user(user_id)

    async def list_plans(self, user_id: int, *, limit: int = 30) -> list[TrainingPlan]:
        async with self._uow:
            return await self._uow.training_plans.list_for_user(user_id, limit=limit)

    async def get_plan_for_user(self, user_id: int, plan_id: int) -> TrainingPlan | None:
        async with self._uow:
            plan = await self._uow.training_plans.get_by_id(plan_id)
            if plan is None or plan.user_id != user_id:
                return None
            return plan

    async def update_plan(
        self,
        user_id: int,
        plan_id: int,
        *,
        start_date: date | None,
        end_date: date | None,
        status: TrainingPlanStatus | None,
    ) -> TrainingPlan | None:
        async with self._uow:
            plan = await self._uow.training_plans.get_by_id(plan_id)
            if plan is None or plan.user_id != user_id:
                return None
            if start_date is not None:
                plan.start_date = start_date
            if end_date is not None:
                plan.end_date = end_date
            if status is not None:
                plan.status = status
            if plan.start_date > plan.end_date:
                raise ValueError("start_date must be <= end_date")
            await self._uow.commit()
        async with self._uow:
            return await self._uow.training_plans.get_by_id(plan_id)

    async def _scheduled_for_user(
        self, user_id: int, scheduled_id: int
    ) -> ScheduledWorkout | None:
        sw = await self._uow.scheduled_workouts.get_by_id(scheduled_id)
        if sw is None or sw.plan is None or sw.plan.user_id != user_id:
            return None
        return sw

    async def update_scheduled_workout(
        self,
        user_id: int,
        scheduled_id: int,
        *,
        scheduled_for: date | None = None,
        week: int | None = None,
        day_of_week: int | None = None,
        volume_multiplier: float | None = None,
        is_completed: bool | None = None,
        completed_at: datetime | None = None,
        perceived_effort: PerceivedEffort | str | None = None,
    ) -> ScheduledWorkout | None:
        async with self._uow:
            sw = await self._scheduled_for_user(user_id, scheduled_id)
            if sw is None:
                return None

            if scheduled_for is not None and scheduled_for != sw.scheduled_for:
                conflict = await self._uow.scheduled_workouts.has_other_on_plan_date(
                    sw.plan_id, scheduled_for, scheduled_id
                )
                if conflict:
                    raise ValueError(
                        "На эту дату уже есть другая тренировка в плане — выберите другую дату"
                    )
                sw.scheduled_for = scheduled_for

            if week is not None:
                sw.week = week
            if day_of_week is not None:
                sw.day_of_week = day_of_week
            if volume_multiplier is not None:
                sw.volume_multiplier = volume_multiplier

            if is_completed is not None:
                sw.is_completed = is_completed
                if is_completed:
                    if completed_at is not None:
                        sw.completed_at = completed_at
                    elif sw.completed_at is None:
                        sw.completed_at = datetime.now(timezone.utc)
                else:
                    sw.completed_at = None
            elif completed_at is not None:
                sw.completed_at = completed_at

            if perceived_effort is not None:
                if perceived_effort == "":
                    sw.perceived_effort = None
                else:
                    parsed = PerceivedEffort.from_raw(perceived_effort)
                    if parsed is None:
                        raise ValueError("perceived_effort должен быть easy | ok | hard")
                    sw.perceived_effort = parsed

            await self._uow.commit()

        async with self._uow:
            return await self._uow.scheduled_workouts.get_by_id(scheduled_id)

    async def replace_session_exercises(
        self,
        user_id: int,
        scheduled_id: int,
        lines: list[tuple[int, int, int | None, int | None, int | None, int | None]],
    ) -> ScheduledWorkout | None:
        """
        lines: (exercise_id, sort_order, sets, reps, duration_seconds, rest_seconds)
        """
        async with self._uow:
            sw = await self._scheduled_for_user(user_id, scheduled_id)
            if sw is None:
                return None

            for ex_id, _, _, _, _, _ in lines:
                ex = await self._uow.exercises.get_by_id(ex_id)
                if ex is None:
                    raise ValueError(f"Упражнение id={ex_id} не найдено")

            await self._uow.scheduled_workouts.delete_session_exercises(scheduled_id)
            await self._uow.flush()

            for exercise_id, sort_order, sets, reps, duration_seconds, rest_seconds in lines:
                exercise = await self._uow.exercises.get_by_id(exercise_id)
                assert exercise is not None
                sw.session_exercises.append(
                    ScheduledWorkoutExercise(
                        exercise=exercise,
                        sort_order=sort_order,
                        sets=sets,
                        reps=reps,
                        duration_seconds=duration_seconds,
                        rest_seconds=rest_seconds,
                    )
                )

            await self._uow.commit()

        async with self._uow:
            return await self._uow.scheduled_workouts.get_by_id(scheduled_id)
