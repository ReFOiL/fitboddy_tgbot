"""
Сервис «план пользователя»: создание или получение активного плана на месяц.
"""
from __future__ import annotations

import structlog

from datetime import date, timedelta

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.workout_scheduler import ScheduledWorkoutItem, WorkoutScheduler
from src.application.use_cases.workout_generator.simple_matcher import MatchedWorkout, SimpleWorkoutMatcher
from src.domain.entities.training_plan import ScheduledWorkout, TrainingPlan, TrainingPlanStatus
from src.presentation.telegram_bot.flows.workouts.link_map_builder import LinkMapBuilder

logger = structlog.get_logger()


def _next_monday(from_date: date) -> date:
    weekday = from_date.weekday()
    if weekday == 0:
        return from_date
    return from_date + timedelta(days=(7 - weekday))


class UserPlanService:
    """Создаёт или возвращает активный план пользователя (на месяц, с расписанием)."""

    def __init__(
        self,
        uow: UnitOfWork,
        matcher: SimpleWorkoutMatcher,
        scheduler: WorkoutScheduler,
        link_map_builder: LinkMapBuilder,
    ) -> None:
        self._uow = uow
        self._matcher = matcher
        self._scheduler = scheduler
        self._link_builder = link_map_builder

    async def create_or_get_active_plan(self, user_id: int) -> TrainingPlan | None:
        """
        Возвращает активный план пользователя.
        Если подходящего плана нет — строит новый (анкета → матчер → расписание) и сохраняет.
        """
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            if user is None:
                return None
            plan = await self._uow.training_plans.get_active_for_user(user_id)
            today = date.today()
            if plan and plan.start_date <= today <= plan.end_date:
                return plan
            # Нет плана или план вне периода — строим новый
            answers = await self._uow.user_answers.list_by_user_id(user_id)
            if not answers:
                logger.warning("user_plan.no_answers", user_id=user_id)
                return None
            templates = await self._uow.workouts.list_all()
            links = await self._uow.question_template_links.list_all()
        if not templates:
            logger.warning("user_plan.no_templates", user_id=user_id)
            return None

        link_map = self._link_builder.build(links)
        matched: list[MatchedWorkout] = await self._matcher.match(
            answers, templates, link_map or None
        )
        if not matched:
            logger.warning("user_plan.no_matches", user_id=user_id, templates_count=len(templates))
            return None

        chosen = list(dict.fromkeys(m.template for m in matched))
        workouts_per_week = len(chosen)
        start_date = _next_monday(today)
        templates_ordered = [m.template for m in matched]
        items: list[ScheduledWorkoutItem] = self._scheduler.schedule_month(
            templates_ordered, workouts_per_week, start_date, weeks=4
        )
        if not items:
            logger.warning("user_plan.schedule_failed", user_id=user_id)
            return None

        async with self._uow:
            plan = TrainingPlan(
                user_id=user_id,
                start_date=min(i.scheduled_for for i in items),
                end_date=max(i.scheduled_for for i in items),
                status=TrainingPlanStatus.ACTIVE,
            )
            await self._uow.training_plans.add(plan)
            await self._uow.flush()
            for item in items:
                sw = ScheduledWorkout(
                    plan_id=plan.id,
                    template_id=item.template.id,
                    scheduled_for=item.scheduled_for,
                    week=item.week,
                    day_of_week=item.day_of_week,
                    volume_multiplier=item.volume_multiplier,
                )
                await self._uow.scheduled_workouts.add(sw)
            await self._uow.commit()
            logger.info(
                "user_plan.created",
                user_id=user_id,
                plan_id=plan.id,
                start_date=plan.start_date.isoformat(),
                end_date=plan.end_date.isoformat(),
                workouts_count=len(items),
                templates_count=len(chosen),
            )
        async with self._uow:
            return await self._uow.training_plans.get_active_for_user(user_id)
