from __future__ import annotations

from datetime import date

import structlog

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.smart_exercise_matcher import SmartExerciseMatcher
from src.application.services.training_plan_generator import TrainingPlanGenerator
from src.application.workout.plan_management.policies import ActivePlanPolicy
from src.domain.entities.training_plan import TrainingPlan

logger = structlog.get_logger()


class UserPlanOrchestrator:
    def __init__(
        self,
        plan_generator: TrainingPlanGenerator,
        active_plan_policy: ActivePlanPolicy | None = None,
    ) -> None:
        self._plan_generator = plan_generator
        self._active_plan_policy = active_plan_policy or ActivePlanPolicy()

    async def get_or_create_active_plan(self, uow: UnitOfWork, user_id: int) -> TrainingPlan | None:
        today = date.today()
        should_reload = False

        async with uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                return None

            active_plan = await uow.training_plans.get_active_for_user(user_id)
            if active_plan is not None and self._active_plan_policy.is_reusable(active_plan, today):
                should_reload = True
            else:
                answers = await uow.user_answers.list_by_user_id(user_id)
                if not answers:
                    logger.warning("user_plan.no_answers", user_id=user_id)
                    return None

                if active_plan is not None:
                    await uow.training_plans.archive_active_for_user(user_id)
                    await uow.flush()
                    logger.info("user_plan.archived_previous", user_id=user_id, old_plan_id=active_plan.id)

                matcher = SmartExerciseMatcher(uow)
                exercises = await matcher.match(answers, limit=50)
                if not exercises:
                    logger.warning("user_plan.exercise_matcher_empty", user_id=user_id)
                    return None

                new_plan = await self._plan_generator.generate_plan(uow, user_id, exercises)
                if new_plan is None:
                    return None

                await uow.commit()
                logger.info(
                    "user_plan.created",
                    user_id=user_id,
                    plan_id=new_plan.id,
                    start_date=new_plan.start_date.isoformat(),
                    end_date=new_plan.end_date.isoformat(),
                )
                should_reload = True

        if not should_reload:
            return None

        async with uow:
            return await uow.training_plans.get_active_for_user(user_id)
