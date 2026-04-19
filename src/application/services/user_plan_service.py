"""
Сервис «план пользователя»: активный месячный план или генерация из каталога упражнений.
"""
from __future__ import annotations

import structlog
from datetime import date

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.smart_exercise_matcher import SmartExerciseMatcher
from src.application.services.training_plan_generator import TrainingPlanGenerator
from src.domain.entities.training_plan import TrainingPlan, TrainingPlanStatus

logger = structlog.get_logger()


class UserPlanService:
    def __init__(
        self,
        uow: UnitOfWork,
        plan_generator: TrainingPlanGenerator,
    ) -> None:
        self._uow = uow
        self._plan_generator = plan_generator

    @staticmethod
    def _plan_covers_date(plan: TrainingPlan, on_date: date) -> bool:
        if plan.status != TrainingPlanStatus.ACTIVE:
            return False
        return plan.start_date <= on_date <= plan.end_date

    @staticmethod
    def _plan_should_roll_forward(plan: TrainingPlan, today: date) -> bool:
        """Пора выдать новый план: период закончился или прошло ≥28 дней от старта."""
        if plan.status != TrainingPlanStatus.ACTIVE:
            return True
        if today > plan.end_date:
            return True
        if (today - plan.start_date).days >= 28:
            return True
        return False

    async def get_or_create_plan(self, user_id: int) -> TrainingPlan | None:
        """
        Активный план в пределах дат — вернуть (из новой сессии, с eager-данными).
        Иначе — заархивировать старые, сгенерировать новый через SmartExerciseMatcher + TrainingPlanGenerator.
        """
        today = date.today()
        reload_from_db = False

        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            if user is None:
                return None

            plan = await self._uow.training_plans.get_active_for_user(user_id)

            if plan is not None and today < plan.start_date:
                reload_from_db = True
            elif plan is not None and self._plan_covers_date(plan, today) and not self._plan_should_roll_forward(
                plan, today
            ):
                reload_from_db = True
            else:
                answers = await self._uow.user_answers.list_by_user_id(user_id)
                if not answers:
                    logger.warning("user_plan.no_answers", user_id=user_id)
                    return None

                if plan is not None:
                    await self._uow.training_plans.archive_active_for_user(user_id)
                    await self._uow.flush()
                    logger.info("user_plan.archived_previous", user_id=user_id, old_plan_id=plan.id)

                matcher = SmartExerciseMatcher(self._uow)
                exercises = await matcher.match(answers, limit=50)
                if not exercises:
                    logger.warning("user_plan.exercise_matcher_empty", user_id=user_id)
                    return None

                new_plan = await self._plan_generator.generate_plan(self._uow, user_id, exercises)
                if new_plan is None:
                    return None

                await self._uow.commit()
                logger.info(
                    "user_plan.created",
                    user_id=user_id,
                    plan_id=new_plan.id,
                    start_date=new_plan.start_date.isoformat(),
                    end_date=new_plan.end_date.isoformat(),
                )
                reload_from_db = True

        if reload_from_db:
            async with self._uow:
                return await self._uow.training_plans.get_active_for_user(user_id)
        return None

    async def create_or_get_active_plan(self, user_id: int) -> TrainingPlan | None:
        """Обратная совместимость со старым именем метода."""
        return await self.get_or_create_plan(user_id)
