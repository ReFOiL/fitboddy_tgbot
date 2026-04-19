"""
Генерация месячного плана: расписание из каталога упражнений + прогрессия объёма по неделям.
"""
from __future__ import annotations

import structlog
import zlib
from datetime import date, timedelta

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.scheduler import (
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
    def _apply_user_training_load(
        sets: int | None,
        reps: int | None,
        duration_seconds: int | None,
        user_load: float,
    ) -> tuple[int | None, int | None, int | None]:
        if user_load <= 0 or abs(user_load - 1.0) < 1e-6:
            return sets, reps, duration_seconds
        new_sets = max(1, round(sets * user_load)) if sets is not None else None
        new_reps = max(1, round(reps * user_load)) if reps is not None else None
        new_dur = (
            max(10, round(duration_seconds * user_load)) if duration_seconds is not None else None
        )
        return new_sets, new_reps, new_dur

    @staticmethod
    def _anchor_monday(from_date: date) -> date:
        """Ближайший понедельник на или после `from_date` (для старта плана)."""
        weekday = from_date.weekday()
        if weekday == 0:
            return from_date
        return from_date + timedelta(days=(7 - weekday))

    @staticmethod
    def _variation_seed(
        *,
        user_id: int,
        anchor: date,
        workouts_per_week: int,
        goal: str,
        exercises: list[Exercise],
    ) -> int:
        ids_part = ",".join(str(e.id) for e in sorted(exercises, key=lambda x: x.id))
        blob = f"{user_id}\n{anchor.isoformat()}\n{workouts_per_week}\n{goal}\n{ids_part}".encode()
        return zlib.crc32(blob) & 0xFFFFFFFF

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
        goal = lookup.get_str("system:goal") or ""
        variation_seed = self._variation_seed(
            user_id=user_id,
            anchor=anchor,
            workouts_per_week=wpw,
            goal=goal,
            exercises=exercises,
        )
        items = self._scheduler.schedule_month(
            exercises,
            wpw,
            anchor,
            weeks=4,
            goal=goal or None,
            variation_seed=variation_seed,
        )
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

        db_user = await uow.users.get_by_id(user_id)
        user_load = float(db_user.training_load_multiplier) if db_user else 1.0

        for item in items:
            sw = ScheduledWorkout(
                plan_id=plan.id,
                scheduled_for=item.scheduled_for,
                week=item.week,
                day_of_week=item.day_of_week,
                volume_multiplier=item.volume_multiplier,
            )
            for line in item.lines:
                sets, reps, dur = self._apply_user_training_load(
                    line.sets, line.reps, line.duration_seconds, user_load
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
            wpw=wpw,
            training_load_multiplier=user_load,
            start_date=plan.start_date.isoformat(),
            end_date=plan.end_date.isoformat(),
        )
        return plan
