from __future__ import annotations

from datetime import date, timedelta

from src.application.interfaces.repositories import UnitOfWork
from src.application.workout.planning.models import PlanningContext, VariationSeedRequest
from src.application.workout.planning.variation_seed_factory import PlanVariationSeedFactory
from src.domain.entities.exercise import Exercise
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import TrainingGoal
from src.shared.utils.profile_answers import AnswerLookup


class PlanningContextFactory:
    def __init__(self, seed_factory: PlanVariationSeedFactory | None = None) -> None:
        self._seed_factory = seed_factory or PlanVariationSeedFactory()

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
        workouts_per_week = lookup.get_int(SystemQuestionKey.WORKOUTS_PER_WEEK)
        if workouts_per_week is None or workouts_per_week < 1:
            workouts_per_week = 3
        workouts_per_week = min(7, max(1, workouts_per_week))

        anchor = start_date or self._anchor_monday(date.today())
        goal = TrainingGoal.from_raw(lookup.get_str(SystemQuestionKey.GOAL))
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
            anchor=anchor,
            variation_seed=variation_seed,
            user_load=user_load,
        )

    @staticmethod
    def _anchor_monday(from_date: date) -> date:
        weekday = from_date.weekday()
        if weekday == 0:
            return from_date
        return from_date + timedelta(days=(7 - weekday))
