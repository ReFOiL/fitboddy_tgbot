"""Короткая пост-тренировочная рефлексия пользователя (уровень энергии)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.base import Base
from src.domain.value_objects.workout_profile import ReflectionEnergy


class WorkoutReflection(Base):
    __tablename__ = "workout_reflections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    scheduled_workout_id: Mapped[int] = mapped_column(
        ForeignKey("scheduled_workouts.id", ondelete="CASCADE"),
        index=True,
    )
    energy: Mapped[ReflectionEnergy] = mapped_column(
        String(16),
        nullable=False,
        doc="low | ok | high",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "scheduled_workout_id", name="uq_workout_reflections_user_scheduled"),
    )

