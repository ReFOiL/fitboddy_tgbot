from __future__ import annotations

import random
from dataclasses import dataclass

from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate
from collections.abc import Callable

from src.shared.utils.profile_answers import AnswerLookup, AnswerLookupMixin


@dataclass(slots=True)
class MatchedWorkout:
    template: WorkoutTemplate
    week: int
    volume_multiplier: float


class SimpleWorkoutMatcher:
    def __init__(
        self,
        lookup_factory: Callable[[list[UserAnswer]], AnswerLookupMixin] | None = None,
    ) -> None:
        self._lookup_factory = lookup_factory or (lambda answers: AnswerLookup(answers))

    async def match(
        self,
        user_answers: list[UserAnswer],
        templates: list[WorkoutTemplate],
        question_links: dict[int, set[int]] | None = None,
    ) -> list[MatchedWorkout]:
        lookup = self._lookup_factory(user_answers)
        goal_value = lookup.get_str("system:goal")
        fitness_value = lookup.get_str("system:level")
        location_value = lookup.get_str("system:workout_location")
        workouts_per_week = lookup.get_int("system:workouts_per_week")
        equipment_values = set(lookup.get_str_list("system:equipment") or [])

        if not goal_value or workouts_per_week is None:
            return []

        filtered = [t for t in templates if t.goal == goal_value]
        if fitness_value == "beginner":
            filtered = [t for t in filtered if t.difficulty == WorkoutDifficulty.LOW]
        if location_value == "home":
            filtered = [t for t in filtered if t.equipment in {"dumbbells", "resistance_bands", "none", None}]
        if equipment_values:
            filtered = [
                t
                for t in filtered
                if (t.equipment in equipment_values) or (t.equipment is None and "none" in equipment_values)
            ]

        if not filtered:
            return []

        chosen = self._select_templates(filtered, user_answers, question_links)
        if not chosen:
            return []
        sample_size = min(workouts_per_week, len(chosen))
        chosen = random.sample(chosen, sample_size)

        result: list[MatchedWorkout] = []
        for week in range(1, 5):
            for template in chosen:
                volume_multiplier = 1.0 + (week - 1) * 0.1
                result.append(MatchedWorkout(template=template, week=week, volume_multiplier=volume_multiplier))
        return result

    def _select_templates(
        self,
        templates: list[WorkoutTemplate],
        user_answers: list[UserAnswer],
        question_links: dict[int, set[int]] | None,
    ) -> list[WorkoutTemplate]:
        if not question_links:
            return templates

        scores: dict[int, int] = {}
        template_by_id = {t.id: t for t in templates if t.id is not None}
        for answer in user_answers:
            key = getattr(answer.question, "key", "") if answer.question is not None else ""
            if not key.startswith("custom:"):
                continue
            try:
                question_id = int(key.split("custom:", 1)[1])
            except ValueError:
                continue
            linked = question_links.get(question_id)
            if not linked:
                continue
            for template_id in linked:
                if template_id in template_by_id:
                    scores[template_id] = scores.get(template_id, 0) + 1

        if not scores:
            return templates

        scored = sorted(
            (template_by_id[template_id] for template_id in scores.keys()),
            key=lambda t: scores.get(t.id or 0, 0),
            reverse=True,
        )
        return scored or templates

