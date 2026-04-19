"""
Умный матчер тренировок с использованием спецификаций и стратегий скоринга.
"""
from __future__ import annotations

import structlog

from dataclasses import dataclass

from src.application.builders.specification_builder import SpecificationBuilder
from src.application.interfaces.repositories import UnitOfWork
from src.application.specifications import Specification
from src.application.strategies import (
    CompositeScoringStrategy,
    CustomQuestionScoring,
    EquipmentOverlapScoring,
    ScoringStrategy,
)
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutTemplate
from src.shared.utils.profile_answers import AnswerLookup, AnswerLookupMixin

logger = structlog.get_logger()


@dataclass(slots=True)
class ScoredWorkoutTemplate:
    """Шаблон тренировки с рассчитанным score."""

    template: WorkoutTemplate
    score: int


class SmartWorkoutMatcher:
    """
    Интеллектуальный матчер тренировок.

    Использует:
    - Specification Pattern для фильтрации
    - Strategy Pattern для скоринга
    - Все доступные ответы пользователя
    """

    def __init__(
        self,
        uow: UnitOfWork,
        scoring_strategy: ScoringStrategy | None = None,
        lookup_factory: type[AnswerLookupMixin] | None = None,
    ) -> None:
        """
        Args:
            uow: Unit of Work для доступа к репозиториям
            scoring_strategy: Стратегия скоринга (по умолчанию композитная)
            lookup_factory: Класс для создания AnswerLookup (для тестирования)
        """
        self._uow = uow
        self._lookup_class = lookup_factory or AnswerLookup
        self._scoring_strategy = scoring_strategy or self._create_default_scoring_strategy()

    def _create_default_scoring_strategy(self) -> ScoringStrategy:
        """Создать стратегию скоринга по умолчанию."""
        return CompositeScoringStrategy(
            [
                (EquipmentOverlapScoring(points_per_match=15), 1),
                (CustomQuestionScoring(default_weight=0), 1),
            ]
        )

    async def match(
        self,
        user_answers: list[UserAnswer],
        limit: int = 20,
    ) -> list[WorkoutTemplate]:
        """
        Найти подходящие шаблоны тренировок для пользователя.

        Args:
            user_answers: Ответы пользователя на вопросы анкеты (все вопросы, включая системные)
            limit: Максимальное количество шаблонов для возврата

        Returns:
            Список шаблонов, отсортированных по убыванию релевантности
        """
        if not user_answers:
            logger.warning("smart_matcher.no_answers")
            return []

        lookup = self._lookup_class(user_answers)

        # Собираем спецификации на основе системных ответов используя Builder
        builder = SpecificationBuilder(lookup, user_answers, self._uow)
        await builder.with_goal()
        await builder.with_difficulty()
        await builder.with_equipment()
        await builder.with_home_friendly()
        await builder.with_intensity()
        await builder.with_age()
        specification = await builder.build()
        if not specification:
            logger.warning("smart_matcher.no_specification")
            return []

        # Применяем спецификацию через репозиторий
        templates = await self._uow.workouts.find_by_specification(specification)
        if not templates:
            logger.warning(
                "smart_matcher.no_matches",
                templates_filtered=0,
            )
            return []

        # Рассчитываем score для каждого шаблона
        scored_templates = await self._score_templates(templates, user_answers)

        # Сортируем по убыванию score
        scored_templates.sort(key=lambda x: x.score, reverse=True)

        # Возвращаем топ-N
        result = [st.template for st in scored_templates[:limit]]
        logger.info(
            "smart_matcher.matched",
            templates_found=len(result),
            templates_filtered=len(templates),
            top_score=scored_templates[0].score if scored_templates else 0,
        )
        return result

    async def _score_templates(
        self, templates: list[WorkoutTemplate], user_answers: list[UserAnswer]
    ) -> list[ScoredWorkoutTemplate]:
        """Рассчитать score для каждого шаблона."""
        scored: list[ScoredWorkoutTemplate] = []
        for template in templates:
            score = await self._scoring_strategy.calculate(template, user_answers, self._uow)
            scored.append(ScoredWorkoutTemplate(template=template, score=score))
        return scored
