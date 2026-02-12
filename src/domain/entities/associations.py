from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.exercise import Exercise
    from src.domain.entities.workout import WorkoutTemplate


class WorkoutExercise(Base):
    """
    Связь WorkoutTemplate <-> Exercise с параметрами выполнения.

    Хранит порядок упражнений внутри шаблона и параметры (подходы/повторения/отдых и т.п.).
    """

    __tablename__ = "workout_exercises"

    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"),
        primary_key=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )

    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workout_template: Mapped["WorkoutTemplate"] = relationship(back_populates="workout_exercises")
    exercise: Mapped["Exercise"] = relationship(back_populates="workout_exercises")

