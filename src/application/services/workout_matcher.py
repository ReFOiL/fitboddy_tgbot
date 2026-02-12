from __future__ import annotations

import structlog

from dataclasses import dataclass
from typing import Protocol

from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate
from src.shared.utils.profile_answers import AnswerLookup, AnswerLookupMixin

logger = structlog.get_logger()


@dataclass(slots=True)
class ScoredTemplate:
    template: WorkoutTemplate
    score: int = 0


class AnswerLookupFactory(Protocol):
    def __call__(self, answers: list[UserAnswer]) -> AnswerLookupMixin: ...


class WorkoutMatcher:
    """
    Простой MVP-матчер.

    - Фильтрует по обязательным параметрам: goal, level, equipment
    - Делает простой скоринг по кастомным вопросам (через question_links)
    - Возвращает 8-10 лучших шаблонов (или меньше, если нет столько)
    """

    def __init__(self, lookup_factory: AnswerLookupFactory | None = None) -> None:
        self._lookup_factory = lookup_factory or (lambda answers: AnswerLookup(answers))

    async def match(
        self,
        user_answers: list[UserAnswer],
        templates: list[WorkoutTemplate],
        question_links: dict[int, set[int]] | None = None,
        limit: int = 10,
    ) -> list[WorkoutTemplate]:
        lookup = self._lookup_factory(user_answers)
        goal_value = lookup.get_str("system:goal")
        level_value = lookup.get_str("system:level")
        equipment_values = set(lookup.get_str_list("system:equipment") or [])

        if not goal_value or not level_value:
            logger.warning(
                "workout_matcher.missing_required",
                has_goal=bool(goal_value),
                has_level=bool(level_value),
            )
            return []

        desired_difficulty = self._difficulty_from_level(level_value)
        filtered = [
            t
            for t in templates
            if (t.goal == goal_value)
            and (t.difficulty == desired_difficulty)
            and self._equipment_ok(t.equipment, equipment_values)
            and getattr(t, "is_active", True)
        ]
        if not filtered:
            logger.warning(
                "workout_matcher.no_matches",
                goal=goal_value,
                level=level_value,
                desired_difficulty=desired_difficulty.value,
                templates_total=len(templates),
            )
            return []

        scored = self._score(filtered, user_answers, question_links)
        scored.sort(key=lambda x: x.score, reverse=True)

        # Если скоринг ничего не добавил — вернем просто первые N (детерминированно)
        if scored and scored[0].score == 0:
            result = [t for t in filtered[: max(1, min(limit, len(filtered)))]]
        else:
            result = [item.template for item in scored[: max(1, min(limit, len(scored)))]]

        logger.info(
            "workout_matcher.matched",
            templates_found=len(result),
            templates_filtered=len(filtered),
            top_score=scored[0].score if scored else 0,
            goal=goal_value,
        )
        return result

    def _score(
        self,
        templates: list[WorkoutTemplate],
        user_answers: list[UserAnswer],
        question_links: dict[int, set[int]] | None,
    ) -> list[ScoredTemplate]:
        scored = [ScoredTemplate(template=t, score=0) for t in templates]
        if not question_links:
            return scored

        template_by_id: dict[int, ScoredTemplate] = {}
        for scored_item in scored:
            if scored_item.template.id is not None:
                template_by_id[scored_item.template.id] = scored_item

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
                linked_item = template_by_id.get(template_id)
                if linked_item is not None:
                    linked_item.score += 1

        return scored

    def _difficulty_from_level(self, level: str) -> WorkoutDifficulty:
        mapping = {
            "beginner": WorkoutDifficulty.LOW,
            "intermediate": WorkoutDifficulty.MEDIUM,
            "advanced": WorkoutDifficulty.HIGH,
        }
        return mapping.get(level, WorkoutDifficulty.MEDIUM)

    def _equipment_ok(self, template_equipment: str | None, user_equipment: set[str]) -> bool:
        # Если шаблон не требует оборудования — подходит всем
        if template_equipment in {None, "", "none"}:
            return True
        # Если у пользователя не заполнено — считаем, что нет
        if not user_equipment:
            return False
        # "none" означает "без оборудования", но не заменяет гантели/штангу
        return template_equipment in user_equipment

