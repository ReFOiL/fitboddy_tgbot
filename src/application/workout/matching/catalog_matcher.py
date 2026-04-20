from __future__ import annotations

import structlog
from time import perf_counter

from src.application.services import metrics as app_metrics
from src.application.workout.matching.eligibility_policy import ExerciseEligibilityPolicy
from src.application.workout.matching.profile_factory import ExerciseMatchingProfileFactory
from src.application.workout.matching.scoring_policy import ExerciseScoringPolicy
from src.domain.entities.exercise import Exercise
from src.domain.entities.user_answer import UserAnswer

logger = structlog.get_logger()
exercise_matching_runs_total = getattr(app_metrics, "exercise_matching_runs_total")
exercise_matching_duration_seconds = getattr(app_metrics, "exercise_matching_duration_seconds")


class CatalogExerciseMatcher:
    def __init__(
        self,
        profile_factory: ExerciseMatchingProfileFactory | None = None,
        eligibility_policy: ExerciseEligibilityPolicy | None = None,
        scoring_policy: ExerciseScoringPolicy | None = None,
    ) -> None:
        self._profile_factory = profile_factory or ExerciseMatchingProfileFactory()
        self._eligibility_policy = eligibility_policy or ExerciseEligibilityPolicy()
        self._scoring_policy = scoring_policy or ExerciseScoringPolicy()

    def match(
        self,
        catalog: list[Exercise],
        user_answers: list[UserAnswer],
        *,
        limit: int = 50,
    ) -> list[Exercise]:
        started_at = perf_counter()
        exercise_matching_runs_total.inc()
        try:
            if not user_answers:
                logger.warning("smart_exercise_matcher.no_answers")
                return []
            if not catalog:
                logger.warning("smart_exercise_matcher.no_catalog")
                return []

            profile = self._profile_factory.build_profile(user_answers)
            candidates = [ex for ex in catalog if self._eligibility_policy.is_eligible(ex, profile)]
            if not candidates:
                logger.warning("smart_exercise_matcher.no_matches_after_filter")
                return []

            scored = [(ex, self._scoring_policy.score(ex, profile)) for ex in candidates]
            scored.sort(key=lambda pair: pair[1], reverse=True)
            result = [exercise for exercise, _ in scored[:limit]]
            logger.info(
                "smart_exercise_matcher.matched",
                catalog=len(catalog),
                candidates=len(candidates),
                returned=len(result),
            )
            return result
        finally:
            exercise_matching_duration_seconds.observe(perf_counter() - started_at)
