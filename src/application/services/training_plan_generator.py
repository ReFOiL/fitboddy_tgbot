"""
Генерация месячного плана: расписание из каталога упражнений + прогрессия объёма по неделям.
"""
from __future__ import annotations

import structlog
from datetime import date

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.scheduler import (
    AbstractWorkoutScheduler,
    WorkoutScheduler,
)
from src.application.workout.scheduler.models import WorkoutScheduleRequest
from src.application.workout.planning import (
    LoadScalingPolicy,
    LoadScalingRequest,
    PlanningContextFactory,
)
from src.domain.entities.exercise import Exercise
from src.domain.entities.training_plan import (
    ScheduledWorkout,
    ScheduledWorkoutExercise,
    TrainingPlan,
    TrainingPlanStatus,
)

logger = structlog.get_logger()


class TrainingPlanGenerator:
    """Строит `TrainingPlan` и `ScheduledWorkout` + строки упражнений из каталога."""

    def __init__(
        self,
        scheduler: AbstractWorkoutScheduler | None = None,
        context_factory: PlanningContextFactory | None = None,
        load_scaling_policy: LoadScalingPolicy | None = None,
    ) -> None:
        self._scheduler: AbstractWorkoutScheduler = scheduler or WorkoutScheduler()
        self._context_factory = context_factory or PlanningContextFactory()
        self._load_scaling_policy = load_scaling_policy or LoadScalingPolicy()

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

        context = await self._context_factory.build_context(
            uow,
            user_id,
            exercises,
            start_date=start_date,
        )
        items = self._scheduler.build_schedule(
            WorkoutScheduleRequest(
                exercises=exercises,
                workouts_per_week=context.workouts_per_week,
                start_date=context.anchor,
                weeks=4,
                goal=context.goal,
                variation_seed=context.variation_seed,
            )
        )
        if not items:
            logger.warning(
                "training_plan_generator.schedule_empty",
                user_id=user_id,
                wpw=context.workouts_per_week,
            )
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
                sets, reps, dur = self._load_scaling_policy.scale(
                    LoadScalingRequest(
                        sets=line.sets,
                        reps=line.reps,
                        duration_seconds=line.duration_seconds,
                        user_load=context.user_load,
                    )
                )
                sw.session_exercises.append(
                    ScheduledWorkoutExercise(
                        exercise=line.exercise,
                        sort_order=line.sort_order,
                        sets=sets,
                        reps=reps,
                        duration_seconds=dur,
                        rest_seconds=line.rest_seconds,
                    )
                )
            await uow.scheduled_workouts.add(sw)

        logger.info(
            "training_plan_generator.plan_built",
            user_id=user_id,
            plan_id=plan.id,
            workouts=len(items),
            wpw=context.workouts_per_week,
            training_load_multiplier=context.user_load,
            start_date=plan.start_date.isoformat(),
            end_date=plan.end_date.isoformat(),
        )
        return plan
