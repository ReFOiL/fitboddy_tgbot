"""
Генерация месячного плана: расписание из каталога упражнений + прогрессия объёма по неделям.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.workout_scheduler import (
    AbstractWorkoutScheduler,
    WorkoutScheduler,
)
from src.domain.entities.exercise import Exercise
from src.domain.entities.training_plan import (
    ScheduledWorkout,
    ScheduledWorkoutExercise,
    TrainingPlan,
    TrainingPlanStatus,
)
from src.shared.utils.profile_answers import AnswerLookup

logger = structlog.get_logger()


class TrainingPlanGenerator:
    """Строит `TrainingPlan` и `ScheduledWorkout` + строки упражнений из каталога."""

    def __init__(self, scheduler: AbstractWorkoutScheduler | None = None) -> None:
        self._scheduler: AbstractWorkoutScheduler = scheduler or WorkoutScheduler()

    @staticmethod
    def _anchor_monday(from_date: date) -> date:
        """Ближайший понедельник на или после `from_date` (для старта плана)."""
        weekday = from_date.weekday()
        if weekday == 0:
            return from_date
        return from_date + timedelta(days=(7 - weekday))

    async def generate_plan(
        self,
        uow: UnitOfWork,
        user_id: int,
        exercises: list[Exercise],
        *,
        start_date: date | None = None,
    ) -> TrainingPlan | None:
        """
        Создаёт план на 4 недели, сохраняет в текущей сессии UoW (без commit).

        `workouts_per_week` читается из ответа `system:workouts_per_week` (по умолчанию 3).
        """
        if not exercises:
            logger.warning("training_plan_generator.no_exercises", user_id=user_id)
            return None

        answers = await uow.user_answers.list_by_user_id(user_id)
        lookup = AnswerLookup(answers)
        wpw = lookup.get_int("system:workouts_per_week")
        if wpw is None or wpw < 1:
            wpw = 3
        wpw = min(7, max(1, wpw))

        anchor = start_date or self._anchor_monday(date.today())
        items = self._scheduler.schedule_month(exercises, wpw, anchor, weeks=4)
        if not items:
            logger.warning("training_plan_generator.schedule_empty", user_id=user_id, wpw=wpw)
            return None

        plan = TrainingPlan(
            user_id=user_id,
            start_date=min(i.scheduled_for for i in items),
            end_date=max(i.scheduled_for for i in items),
            status=TrainingPlanStatus.ACTIVE,
        )
        await uow.training_plans.add(plan)
        await uow.flush()

        for item in items:
            sw = ScheduledWorkout(
                plan_id=plan.id,
                scheduled_for=item.scheduled_for,
                week=item.week,
                day_of_week=item.day_of_week,
                volume_multiplier=item.volume_multiplier,
            )
            for line in item.lines:
                sw.session_exercises.append(
                    ScheduledWorkoutExercise(
                        exercise=line.exercise,
                        sort_order=line.sort_order,
                        sets=line.sets,
                        reps=line.reps,
                        duration_seconds=line.duration_seconds,
                        rest_seconds=line.rest_seconds,
                    )
                )
            await uow.scheduled_workouts.add(sw)

        logger.info(
            "training_plan_generator.plan_built",
            user_id=user_id,
            plan_id=plan.id,
            workouts=len(items),
            wpw=wpw,
            start_date=plan.start_date.isoformat(),
            end_date=plan.end_date.isoformat(),
        )
        return plan
