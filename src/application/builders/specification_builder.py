"""
Builder для построения спецификаций фильтрации тренировок (Builder Pattern).
"""
from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.specifications import (
    AgeSpecification,
    AndSpecification,
    DifficultySpecification,
    EquipmentSpecification,
    GoalSpecification,
    HomeFriendlySpecification,
    IntensitySpecification,
    Specification,
)
from src.domain.entities.user_answer import UserAnswer
from src.shared.utils.profile_answers import AnswerLookupMixin, UserAnswerExtractor


class SpecificationBuilder:
    """Builder для построения комбинированной спецификации."""

    def __init__(
        self,
        lookup: AnswerLookupMixin,
        user_answers: list[UserAnswer],
        uow: UnitOfWork,
    ) -> None:
        """
        Args:
            lookup: AnswerLookup для получения значений ответов
            user_answers: Все ответы пользователя
            uow: Unit of Work для доступа к репозиториям
        """
        self._lookup = lookup
        self._user_answers = user_answers
        self._uow = uow
        self._specs: list[Specification] = []
        self._user_equipment_ids: list[int] | None = None

    async def with_goal(self) -> SpecificationBuilder:
        """Добавить спецификацию по цели (обязательно)."""
        goal = self._lookup.get_str("system:goal")
        if goal:
            self._specs.append(GoalSpecification(goal))
        return self

    async def with_difficulty(self) -> SpecificationBuilder:
        """Добавить спецификацию по уровню сложности."""
        level = self._lookup.get_str("system:level")
        if level:
            self._specs.append(DifficultySpecification(level))
        return self

    async def with_equipment(self) -> SpecificationBuilder:
        """Добавить спецификацию по оборудованию."""
        equipment_ids = await self._get_user_equipment_ids()
        if equipment_ids:
            self._specs.append(EquipmentSpecification(equipment_ids))
        return self

    async def with_home_friendly(self) -> SpecificationBuilder:
        """Добавить спецификацию для домашних тренировок (если место = дом)."""
        location = self._lookup.get_str("system:workout_location")
        if location == "home":
            equipment_ids = await self._get_user_equipment_ids()
            self._specs.append(HomeFriendlySpecification(equipment_ids))
        return self

    async def with_intensity(self) -> SpecificationBuilder:
        """Добавить спецификацию по интенсивности."""
        activity = self._lookup.get_str("system:activity")
        if activity:
            self._specs.append(IntensitySpecification(activity))
        return self

    async def with_age(self) -> SpecificationBuilder:
        """Добавить спецификацию по возрасту."""
        age = self._lookup.get_int("system:age")
        if age:
            self._specs.append(AgeSpecification(age))
        return self

    async def build(self) -> Specification | None:
        """
        Построить финальную спецификацию.
        
        Returns:
            Комбинированная спецификация или None если нет спецификаций
        """
        if not self._specs:
            return None

        if len(self._specs) == 1:
            return self._specs[0]

        return AndSpecification(*self._specs)

    async def _get_user_equipment_ids(self) -> list[int]:
        """Получить ID оборудования пользователя (с кешированием)."""
        if self._user_equipment_ids is not None:
            return self._user_equipment_ids

        equipment_answer = UserAnswerExtractor.find_by_question_key(
            self._user_answers, "system:equipment"
        )
        if not equipment_answer:
            self._user_equipment_ids = []
            return []

        equipment_names = UserAnswerExtractor.extract_equipment_names(equipment_answer)
        if not equipment_names:
            self._user_equipment_ids = []
            return []

        # Находим Equipment по name (Equipment - справочник)
        equipment_ids: list[int] = []
        for eq_name in equipment_names:
            equipment = await self._uow.equipment.get_by_name(eq_name)
            if equipment:
                equipment_ids.append(equipment.id)

        self._user_equipment_ids = equipment_ids
        return equipment_ids
