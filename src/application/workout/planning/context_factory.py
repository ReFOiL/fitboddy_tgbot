from __future__ import annotations

from datetime import date, timedelta

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.metrics import (
    plan_adherence_score,
    plan_cycle_completion_rate,
)
from src.application.workout.planning.adherence_policy import AdherenceScorePolicy
from src.application.workout.planning.defaults_policy import PlanningDefaultsPolicy
from src.application.workout.planning.models import PlanningContext, VariationSeedRequest
from src.application.workout.planning.phase_progression_policy import GoalPhaseProgressionPolicy
from src.application.workout.planning.reflection_readiness_policy import (
    ReflectionReadinessPolicy,
)
from src.application.workout.planning.variation_seed_factory import PlanVariationSeedFactory
from src.domain.entities.exercise import Exercise
from src.domain.entities.training_plan import TrainingPlan
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import TrainingGoal
from src.shared.utils.profile_answers import AnswerLookup


class PlanningContextFactory:
    def __init__(
        self,
        seed_factory: PlanVariationSeedFactory | None = None,
        defaults_policy: PlanningDefaultsPolicy | None = None,
        adherence_policy: AdherenceScorePolicy | None = None,
        phase_policy: GoalPhaseProgressionPolicy | None = None,
        reflection_readiness_policy: ReflectionReadinessPolicy | None = None,
    ) -> None:
        self._seed_factory = seed_factory or PlanVariationSeedFactory()
        self._defaults_policy = defaults_policy or PlanningDefaultsPolicy()
        self._adherence_policy = adherence_policy or AdherenceScorePolicy()
        self._phase_policy = phase_policy or GoalPhaseProgressionPolicy()
        self._reflection_readiness_policy = (
            reflection_readiness_policy or ReflectionReadinessPolicy()
        )

    async def build_context(
        self,
        uow: UnitOfWork,
        user_id: int,
        exercises: list[Exercise],
        *,
        start_date: date | None = None,
    ) -> PlanningContext:
        answers = await uow.user_answers.list_by_user_id(user_id)
        lookup = AnswerLookup(answers)
        goal = TrainingGoal.from_raw(lookup.get_str(SystemQuestionKey.GOAL))
        level = self._defaults_policy.resolve_level(lookup.get_str(SystemQuestionKey.LEVEL))
        recent_plans = await uow.training_plans.list_for_user(user_id, limit=6)
        has_previous_plans = bool(recent_plans)
        is_first_plan = not has_previous_plans
        cycle_index = len(recent_plans) + 1
        previous_adherence = await self._last_cycle_adherence(uow, recent_plans)
        readiness_multiplier = await self._readiness_multiplier(uow, user_id)
        phase = self._phase_policy.resolve_phase(cycle_index=cycle_index, goal=goal, level=level)
        workouts_per_week = self._defaults_policy.resolve_workouts_per_week(
            lookup.get_int(SystemQuestionKey.WORKOUTS_PER_WEEK),
            level=level,
            goal=goal,
            is_first_plan=is_first_plan,
            adherence_score=previous_adherence,
            readiness_multiplier=readiness_multiplier,
        )

        anchor = start_date or self._anchor_monday(date.today())
        variation_seed = self._seed_factory.build_seed(
            VariationSeedRequest(
                user_id=user_id,
                anchor=anchor,
                workouts_per_week=workouts_per_week,
                goal=goal,
                exercises=exercises,
            )
        )
        db_user = await uow.users.get_by_id(user_id)
        user_load = float(db_user.training_load_multiplier) if db_user else 1.0
        return PlanningContext(
            workouts_per_week=workouts_per_week,
            goal=goal,
            level=level,
            phase=phase.name,
            cycle_index=cycle_index,
            anchor=anchor,
            variation_seed=variation_seed,
            adherence_score=previous_adherence,
            readiness_multiplier=readiness_multiplier,
            weekly_volume_by_week=phase.weekly_volume_by_week,
            user_load=user_load,
            is_first_plan=is_first_plan,
        )

    @staticmethod
    def _anchor_monday(from_date: date) -> date:
        weekday = from_date.weekday()
        if weekday == 0:
            return from_date
        return from_date + timedelta(days=(7 - weekday))

    async def _last_cycle_adherence(
        self, uow: UnitOfWork, recent_plans: list[TrainingPlan]
    ) -> float:
        if not recent_plans:
            return 1.0
        last_plan = recent_plans[0]
        workouts = await uow.scheduled_workouts.list_by_plan_id(last_plan.id)
        adherence = self._adherence_policy.calculate(workouts)
        plan_adherence_score.observe(adherence)
        plan_cycle_completion_rate.observe(adherence)
        return adherence

    async def _readiness_multiplier(self, uow: UnitOfWork, user_id: int) -> float:
        recent_energies = await uow.workout_reflections.list_last_energy_levels(user_id, limit=5)
        return self._reflection_readiness_policy.readiness_multiplier(recent_energies)
