from __future__ import annotations

from datetime import datetime, timezone

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.metrics import workout_retention_signal_total
from src.application.services.user_plan_service import UserPlanService
from src.application.use_cases.workout.query.errors import WorkoutQueryPlanNotFound
from src.application.use_cases.workout.query.models import (
    MyPlanViewData,
    WorkoutCycleProgressSummary,
)
from src.application.use_cases.workout.query.user_resolver import WorkoutTelegramUserResolver
from src.application.workout.plan_management import WorkoutCycleProgressService
from src.application.workout.planning import (
    GoalPhaseProgressionPolicy,
    PlanningDefaultsPolicy,
)
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import ReflectionEnergy, TrainingGoal
from src.shared.utils.profile_answers import AnswerLookup

class GetMyPlanUseCase:
    def __init__(self, uow: UnitOfWork, user_plan_service: UserPlanService) -> None:
        self._uow = uow
        self._user_plan_service = user_plan_service
        self._user_resolver = WorkoutTelegramUserResolver(uow)
        self._progress_service = WorkoutCycleProgressService()
        self._defaults = PlanningDefaultsPolicy()
        self._phase_policy = GoalPhaseProgressionPolicy()

    async def get_plan(self, tg_user_id: int) -> MyPlanViewData:
        user = await self._user_resolver.resolve_user(tg_user_id)
        self._record_retention_signal(user.created_at)
        plan = await self._user_plan_service.get_or_create_plan(user.id)
        if plan is None:
            raise WorkoutQueryPlanNotFound()
        progress = await self._build_progress_summary(user.id, plan.id)
        recent_difficulties, recent_energies = await self._build_feedback_signals(user.id)
        return MyPlanViewData(
            user_id=user.id,
            telegram_id=tg_user_id,
            plan=plan,
            progress=progress,
            recent_difficulties=recent_difficulties,
            recent_energies=recent_energies,
        )

    def _record_retention_signal(self, created_at: datetime) -> None:
        created_at_utc = (
            created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=timezone.utc)
        )
        age_days = (datetime.now(timezone.utc) - created_at_utc).days
        if age_days >= 30:
            workout_retention_signal_total.labels(window="d30").inc()
        elif age_days >= 7:
            workout_retention_signal_total.labels(window="d7").inc()
        else:
            workout_retention_signal_total.labels(window="d0").inc()

    async def _build_progress_summary(
        self, user_id: int, active_plan_id: int
    ) -> WorkoutCycleProgressSummary | None:
        async with self._uow:
            plans = await self._uow.training_plans.list_for_user(user_id, limit=10)
            current_plan = next((item for item in plans if item.id == active_plan_id), None)
            if current_plan is None:
                return None
            current_workouts = await self._uow.scheduled_workouts.list_by_plan_id(current_plan.id)

            previous_plan = next((item for item in plans if item.id != current_plan.id), None)
            previous_workouts = (
                await self._uow.scheduled_workouts.list_by_plan_id(previous_plan.id)
                if previous_plan is not None
                else []
            )
            answers = await self._uow.user_answers.list_by_user_id(user_id)
            lookup = AnswerLookup(answers)
            goal = TrainingGoal.from_raw(lookup.get_str(SystemQuestionKey.GOAL))
            level = self._defaults.resolve_level(lookup.get_str(SystemQuestionKey.LEVEL))
            cycle_index = len(plans)
            phase = self._phase_policy.resolve_phase(cycle_index=cycle_index, goal=goal, level=level)
            workouts_per_week = max(1, round(len(current_workouts) / 4)) if current_workouts else 0
            return self._progress_service.build_summary(
                current_plan=current_plan,
                current_workouts=current_workouts,
                previous_plan=previous_plan,
                previous_workouts=previous_workouts,
                cycle_index=cycle_index,
                phase=phase.name,
                workouts_per_week=workouts_per_week,
            )

    async def _build_feedback_signals(
        self, user_id: int
    ) -> tuple[list[str], list[ReflectionEnergy]]:
        async with self._uow:
            recent_difficulties = await self._uow.workout_feedback.list_last_difficulties(user_id, limit=3)
            recent_energies = await self._uow.workout_reflections.list_last_energy_levels(user_id, limit=3)
        return recent_difficulties, recent_energies
