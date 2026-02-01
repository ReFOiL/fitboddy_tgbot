from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


workout_exercises = Table(
    "workout_exercises",
    Base.metadata,
    Column("workout_id", ForeignKey("workout_templates.id"), primary_key=True),
    Column("exercise_id", ForeignKey("exercises.id"), primary_key=True),
)


class WorkoutDifficulty(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[WorkoutDifficulty] = mapped_column(Enum(WorkoutDifficulty))
    equipment: Mapped[str | None] = mapped_column(String(128))
    days_per_week: Mapped[int] = mapped_column(Integer, default=3)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="workout_templates", secondary=workout_exercises
    )
    user: Mapped["User | None"] = relationship(back_populates="workouts")
    linked_questions: Mapped[list["CustomQuestion"]] = relationship(
        secondary="question_template_links",
        back_populates="workout_templates",
    )


from src.domain.entities.user import User  # noqa: E402  # isort:skip
from src.domain.entities.exercise import Exercise  # noqa: E402  # isort:skip
from src.domain.entities.questionnaire import CustomQuestion  # noqa: E402  # isort:skip

