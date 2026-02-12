from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.associations import WorkoutExercise
    from src.domain.entities.exercise import Exercise
    from src.domain.entities.questionnaire import CustomQuestion
    from src.domain.entities.training_plan import ScheduledWorkout
    from src.domain.entities.user import User


class WorkoutDifficulty(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[WorkoutDifficulty] = mapped_column(
        Enum(WorkoutDifficulty, name="workoutdifficulty")
    )
    equipment: Mapped[str | None] = mapped_column(String(128))
    days_per_week: Mapped[int] = mapped_column(Integer, default=3)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout_template",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.sort_order",
    )
    exercises: Mapped[list["Exercise"]] = relationship(
        secondary="workout_exercises",
        viewonly=True,
        back_populates="workout_templates",
    )
    user: Mapped["User | None"] = relationship(back_populates="workouts")
    linked_questions: Mapped[list["CustomQuestion"]] = relationship(
        secondary="question_template_links",
        back_populates="workout_templates",
    )
    scheduled_workouts: Mapped[list["ScheduledWorkout"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
    )

