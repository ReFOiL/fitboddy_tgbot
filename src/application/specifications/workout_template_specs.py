"""
Спецификации для фильтрации шаблонов тренировок (Specification Pattern).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import Select, and_, not_, or_, select as sql_select
from sqlalchemy.orm import selectinload

from src.domain.entities.associations import (
    workout_template_equipment,
)
from src.domain.entities.equipment import Equipment
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


class Specification(ABC):
    """Базовый интерфейс спецификации."""

    @abstractmethod
    def apply(self, stmt: Select) -> Select:
        """Применить спецификацию к SQLAlchemy Select."""
        pass

    def __and__(self, other: Specification) -> AndSpecification:
        """Композиция через AND."""
        return AndSpecification(self, other)

    def __or__(self, other: Specification) -> OrSpecification:
        """Композиция через OR."""
        return OrSpecification(self, other)


class AndSpecification(Specification):
    """Композиция спецификаций через AND."""

    def __init__(self, *specs: Specification) -> None:
        self.specs = list(specs)

    def apply(self, stmt: Select) -> Select:
        for spec in self.specs:
            stmt = spec.apply(stmt)
        return stmt


class OrSpecification(Specification):
    """Композиция спецификаций через OR."""

    def __init__(self, *specs: Specification) -> None:
        self.specs = list(specs)

    def apply(self, stmt: Select) -> Select:
        # Для OR нужна более сложная логика через union или подзапросы
        # Для простоты пока не реализуем, используем только AND
        raise NotImplementedError("OR specification not implemented yet")


class GoalSpecification(Specification):
    """Фильтр по цели тренировки."""

    def __init__(self, goal: str) -> None:
        self.goal = goal

    def apply(self, stmt: Select) -> Select:
        return stmt.where(WorkoutTemplate.goal == self.goal)


class DifficultySpecification(Specification):
    """Фильтр по уровню сложности (переводит уровень в диапазон)."""

    # Маппинг уровня подготовки на диапазон сложности
    LEVEL_MAP: dict[str, tuple[WorkoutDifficulty, WorkoutDifficulty]] = {
        "beginner": (WorkoutDifficulty.LOW, WorkoutDifficulty.LOW),
        "intermediate": (WorkoutDifficulty.LOW, WorkoutDifficulty.MEDIUM),
        "advanced": (WorkoutDifficulty.MEDIUM, WorkoutDifficulty.HIGH),
    }

    def __init__(self, level: str) -> None:
        self.level = level
        self.min_dif, self.max_dif = self.LEVEL_MAP.get(
            level, (WorkoutDifficulty.LOW, WorkoutDifficulty.HIGH)
        )

    def apply(self, stmt: Select) -> Select:
        # Для enum нужно сравнивать значения
        if self.min_dif == self.max_dif:
            return stmt.where(WorkoutTemplate.difficulty == self.min_dif)
        # Для диапазона используем IN
        difficulties = []
        all_difficulties = list(WorkoutDifficulty)
        min_idx = all_difficulties.index(self.min_dif)
        max_idx = all_difficulties.index(self.max_dif)
        for idx in range(min_idx, max_idx + 1):
            difficulties.append(all_difficulties[idx])
        return stmt.where(WorkoutTemplate.difficulty.in_(difficulties))


class EquipmentSpecification(Specification):
    """
    Фильтр по оборудованию: шаблон подходит, если все требуемое оборудование
    есть у пользователя.
    """

    def __init__(self, user_equipment_ids: list[int]) -> None:
        self.user_equipment_ids = user_equipment_ids

    def apply(self, stmt: Select) -> Select:
        if not self.user_equipment_ids:
            # Если у пользователя нет оборудования, разрешаем только шаблоны без оборудования
            templates_with_equipment = sql_select(workout_template_equipment.c.workout_template_id).distinct()
            return stmt.where(~WorkoutTemplate.id.in_(templates_with_equipment))

        # Подзапрос: шаблоны, у которых есть оборудование, которого нет у пользователя
        missing_equipment = (
            sql_select(workout_template_equipment.c.workout_template_id)
            .where(
                ~workout_template_equipment.c.equipment_id.in_(self.user_equipment_ids)
            )
            .distinct()
        )

        # Исключаем такие шаблоны
        return stmt.where(~WorkoutTemplate.id.in_(missing_equipment))


class HomeFriendlySpecification(Specification):
    """
    Фильтр для домашних тренировок: разрешены только шаблоны с домашним оборудованием.
    """

    def __init__(self, user_equipment_ids: list[int] | None = None) -> None:
        self.user_equipment_ids = user_equipment_ids or []

    def apply(self, stmt: Select) -> Select:
        # Загружаем связь с оборудованием
        stmt = stmt.options(selectinload(WorkoutTemplate.required_equipment))

        # Шаблоны, у которых есть недомашнее оборудование
        non_home_equipment_ids = (
            sql_select(Equipment.id).where(Equipment.is_home_friendly.is_(False)).scalar_subquery()
        )
        
        non_home_templates = (
            sql_select(workout_template_equipment.c.workout_template_id)
            .where(workout_template_equipment.c.equipment_id.in_(non_home_equipment_ids))
            .distinct()
        )

        # Разрешаем шаблоны без оборудования или только с домашним (исключаем те, у которых есть недомашнее)
        return stmt.where(~WorkoutTemplate.id.in_(non_home_templates))


class IntensitySpecification(Specification):
    """Фильтр по интенсивности (на основе уровня активности)."""

    # Маппинг уровня активности на максимальную интенсивность
    ACTIVITY_INTENSITY_MAP: dict[str, float] = {
        "sedentary": 1.0,
        "light": 1.2,
        "moderate": 1.5,
        "active": 2.0,
        "very_active": 2.5,
    }

    def __init__(self, activity_level: str) -> None:
        self.max_intensity = self.ACTIVITY_INTENSITY_MAP.get(activity_level, 2.0)

    def apply(self, stmt: Select) -> Select:
        return stmt.where(WorkoutTemplate.intensity_factor <= self.max_intensity)


class AgeSpecification(Specification):
    """Фильтр по возрасту пользователя."""

    def __init__(self, age: int) -> None:
        self.age = age

    def apply(self, stmt: Select) -> Select:
        conditions = []
        # Если указан min_age, возраст должен быть >= min_age
        conditions.append(
            or_(WorkoutTemplate.min_age.is_(None), WorkoutTemplate.min_age <= self.age)
        )
        # Если указан max_age, возраст должен быть <= max_age
        conditions.append(
            or_(WorkoutTemplate.max_age.is_(None), WorkoutTemplate.max_age >= self.age)
        )
        return stmt.where(and_(*conditions))
