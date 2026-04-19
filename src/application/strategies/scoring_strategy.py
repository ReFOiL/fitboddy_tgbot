"""
Стратегии скоринга для расчёта релевантности тренировок (Strategy Pattern).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutTemplate
from src.shared.utils.profile_answers import UserAnswerExtractor


class ScoringStrategy(ABC):
    """Базовый интерфейс стратегии скоринга."""

    @abstractmethod
    async def calculate(
        self,
        template: WorkoutTemplate,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> int:
        """
        Рассчитать score для шаблона тренировки.

        Args:
            template: Шаблон тренировки
            user_answers: Ответы пользователя
            uow: Unit of Work для доступа к репозиториям

        Returns:
            Score (целое число, может быть отрицательным)
        """
        pass


class BaseScoreStrategy(ScoringStrategy):
    """Базовый скоринг: все шаблоны получают одинаковый базовый score."""

    def __init__(self, base_score: int = 100) -> None:
        self.base_score = base_score

    async def calculate(
        self,
        template: WorkoutTemplate,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> int:
        return self.base_score


class EquipmentOverlapScoring(ScoringStrategy):
    """
    Бонус за совпадение оборудования: чем больше оборудования шаблона
    совпадает с пользовательским, тем выше score.
    """

    def __init__(self, points_per_match: int = 10) -> None:
        self.points_per_match = points_per_match

    async def calculate(
        self,
        template: WorkoutTemplate,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> int:
        if not template.required_equipment:
            return 0

        # Получаем ID оборудования пользователя
        user_equipment_ids = await self._get_user_equipment_ids(user_answers, uow)
        if not user_equipment_ids:
            return 0

        template_equipment_ids = {eq.id for eq in template.required_equipment}
        overlap = len(template_equipment_ids & set(user_equipment_ids))
        return overlap * self.points_per_match

    async def _get_user_equipment_ids(
        self, user_answers: list[UserAnswer], uow: UnitOfWork
    ) -> list[int]:
        """Получить ID оборудования пользователя из ответов."""
        equipment_answer = UserAnswerExtractor.find_by_question_key(user_answers, "system:equipment")
        if not equipment_answer:
            return []

        equipment_names = UserAnswerExtractor.extract_equipment_names(equipment_answer)
        if not equipment_names:
            return []

        # Находим Equipment по name (Equipment - справочник)
        equipment_ids: list[int] = []
        for eq_name in equipment_names:
            equipment = await uow.equipment.get_by_name(eq_name)
            if equipment:
                equipment_ids.append(equipment.id)

        return equipment_ids


class CustomQuestionScoring(ScoringStrategy):
    """
    Скоринг на основе весов кастомных вопросов.
    Использует таблицу custom_question_scoring_weights.
    """

    def __init__(self, default_weight: int = 0) -> None:
        self.default_weight = default_weight

    async def calculate(
        self,
        template: WorkoutTemplate,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> int:
        if not template.linked_questions:
            return 0

        total_score = 0
        for question in template.linked_questions:
            # Находим ответ пользователя на этот вопрос
            user_answer = None
            for answer in user_answers:
                if answer.question_id == question.id:
                    user_answer = answer
                    break

            if not user_answer:
                continue

            # Получаем строковое представление ответа
            answer_value = self._get_answer_value(user_answer)
            if not answer_value:
                continue

            # Получаем вес из таблицы
            weight = await uow.custom_questions.get_scoring_weight(
                question.id, answer_value
            )
            if weight is not None:
                total_score += weight
            else:
                total_score += self.default_weight

        return total_score

    def _get_answer_value(self, answer: UserAnswer) -> str | None:
        """Получить строковое представление ответа."""
        value = UserAnswerExtractor.extract_value(answer)
        return str(value) if value is not None else None


class CompositeScoringStrategy(ScoringStrategy):
    """
    Композитная стратегия: агрегирует несколько стратегий с весами.
    """

    def __init__(
        self, strategies: list[tuple[ScoringStrategy, int]]
    ) -> None:
        """
        Args:
            strategies: Список кортежей (стратегия, вес стратегии)
        """
        self.strategies = strategies

    async def calculate(
        self,
        template: WorkoutTemplate,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> int:
        total = 0
        for strategy, weight in self.strategies:
            score = await strategy.calculate(template, user_answers, uow)
            total += score * weight
        return total
