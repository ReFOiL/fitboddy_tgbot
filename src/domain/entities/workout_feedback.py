"""Фиксация субъективной сложности после тренировки (отдельно от поля на ScheduledWorkout для истории)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.base import Base


class WorkoutFeedback(Base):
    """
    Один ряд на завершённую тренировку (user + scheduled_workout).
    difficulty: easy | normal | hard (ok из бота сохраняется как normal).
    """

    __tablename__ = "workout_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    scheduled_workout_id: Mapped[int] = mapped_column(
        ForeignKey("scheduled_workouts.id", ondelete="CASCADE"),
        index=True,
    )
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "scheduled_workout_id", name="uq_workout_feedback_user_scheduled"),
    )
