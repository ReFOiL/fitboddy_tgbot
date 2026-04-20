from __future__ import annotations

import structlog
from time import perf_counter

from src.application.services.metrics import (
    exercise_matching_duration_seconds,
    exercise_matching_runs_total,
    plan_novelty_ratio,
)
from src.application.workout.matching.eligibility_policy import ExerciseEligibilityPolicy
from src.application.workout.matching.profile_factory import ExerciseMatchingProfileFactory
from src.application.workout.matching.scoring_policy import ExerciseScoringPolicy
from src.domain.entities.exercise import Exercise
from src.domain.entities.user_answer import UserAnswer

logger = structlog.get_logger()


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
        recent_exercise_ids: set[int] | None = None,
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
            result = self._pick_with_novelty_control(
                scored=scored,
                limit=limit,
                recent_exercise_ids=recent_exercise_ids or set(),
            )
            logger.info(
                "smart_exercise_matcher.matched",
                catalog=len(catalog),
                candidates=len(candidates),
                returned=len(result),
            )
            return result
        finally:
            exercise_matching_duration_seconds.observe(perf_counter() - started_at)

    @staticmethod
    def _diversify_by_category(scored: list[tuple[Exercise, int]], limit: int) -> list[Exercise]:
        by_category: dict[str, list[Exercise]] = {}
        for exercise, _score in scored:
            category = getattr(exercise, "workout_category", None) or "full_body"
            by_category.setdefault(category, []).append(exercise)
        ordered_categories = sorted(by_category.keys())
        result: list[Exercise] = []
        cursor = 0
        while len(result) < limit and ordered_categories:
            category = ordered_categories[cursor % len(ordered_categories)]
            cursor += 1
            bucket = by_category[category]
            if not bucket:
                continue
            result.append(bucket.pop(0))
            if not bucket:
                ordered_categories.remove(category)
        return result

    def _pick_with_novelty_control(
        self,
        *,
        scored: list[tuple[Exercise, int]],
        limit: int,
        recent_exercise_ids: set[int],
    ) -> list[Exercise]:
        if not recent_exercise_ids:
            return self._diversify_by_category(scored, limit)
        novelty_penalty = 3
        reweighted: list[tuple[Exercise, int]] = []
        for exercise, base in scored:
            adjusted = base - novelty_penalty if exercise.id in recent_exercise_ids else base
            reweighted.append((exercise, adjusted))
        reweighted.sort(key=lambda pair: pair[1], reverse=True)

        fresh = [pair for pair in reweighted if pair[0].id not in recent_exercise_ids]
        repeated = [pair for pair in reweighted if pair[0].id in recent_exercise_ids]
        minimum_new = min(len(fresh), max(1, int(limit * 0.35)))

        picked_new = self._diversify_by_category(fresh, minimum_new)
        remaining = max(0, limit - len(picked_new))
        picked_old = self._diversify_by_category(repeated, remaining)
        if len(picked_new) + len(picked_old) < limit:
            already = {exercise.id for exercise in [*picked_new, *picked_old]}
            fill_pool = [exercise for exercise, _score in reweighted if exercise.id not in already]
            picked_old.extend(fill_pool[: max(0, limit - len(picked_new) - len(picked_old))])
        result = [*picked_new, *picked_old][:limit]
        plan_novelty_ratio.observe(self._novelty_ratio(result, recent_exercise_ids))
        return result

    @staticmethod
    def _novelty_ratio(exercises: list[Exercise], recent_exercise_ids: set[int]) -> float:
        if not exercises:
            return 0.0
        fresh = sum(1 for exercise in exercises if exercise.id not in recent_exercise_ids)
        return round(fresh / len(exercises), 3)
