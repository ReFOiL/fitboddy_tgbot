from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.associations import WorkoutExercise
    from src.domain.entities.exercise import Exercise
    from src.domain.entities.questionnaire import CustomQuestion
    from src.domain.entities.training_plan import ScheduledWorkout
    from src.domain.entities.user import User
    from src.domain.entities.equipment import Equipment


class WorkoutDifficulty(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(String(32), index=True)  # Индекс для фильтрации
    difficulty: Mapped[WorkoutDifficulty] = mapped_column(
        Enum(WorkoutDifficulty, name="workoutdifficulty"),
        index=True,  # Индекс для фильтрации
    )
    days_per_week: Mapped[int] = mapped_column(Integer, default=3)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # NULL = глобальный шаблон, NOT NULL = пользовательский шаблон
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_global: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )  # Флаг глобального шаблона (альтернатива проверке user_id IS NULL)
    
    # Новые поля для улучшенного подбора
    intensity_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    workout_category: Mapped[str] = mapped_column(String(50), nullable=False, default="full_body", index=True)  # Индекс для фильтрации
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        # Составной индекс для частых запросов: активные шаблоны по цели и сложности
        Index("idx_workout_active_goal_difficulty", "is_active", "goal", "difficulty"),
        # Составной индекс для глобальных активных шаблонов (часто используются в матчинге)
        Index("idx_workout_global_active", "is_global", "is_active"),
        # CHECK: min_age <= max_age если оба указаны
        CheckConstraint(
            "(min_age IS NULL) OR (max_age IS NULL) OR (min_age <= max_age)",
            name="ck_workout_age_range",
        ),
        # CHECK: intensity_factor > 0
        CheckConstraint(
            "intensity_factor > 0",
            name="ck_workout_intensity_positive",
        ),
        # CHECK: days_per_week в разумных пределах
        CheckConstraint(
            "days_per_week >= 1 AND days_per_week <= 7",
            name="ck_workout_days_per_week",
        ),
        # CHECK: is_global = true если user_id IS NULL, и наоборот
        CheckConstraint(
            "(is_global = true AND user_id IS NULL) OR (is_global = false AND user_id IS NOT NULL)",
            name="ck_workout_global_consistency",
        ),
    )

    workout_exercises: Mapped[list[WorkoutExercise]] = relationship(
        back_populates="workout_template",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.sort_order",
    )
    exercises: Mapped[list[Exercise]] = relationship(
        secondary="workout_exercises",
        viewonly=True,
        back_populates="workout_templates",
    )
    user: Mapped[User | None] = relationship(back_populates="workouts")
    linked_questions: Mapped[list[CustomQuestion]] = relationship(
        secondary="question_template_links",
        back_populates="workout_templates",
    )
    scheduled_workouts: Mapped[list[ScheduledWorkout]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
    )
    # Связи с оборудованием (Equipment - справочник, управляется через админку)
    required_equipment: Mapped[list[Equipment]] = relationship(
        secondary="workout_template_equipment",
        back_populates="workout_templates",
    )
