from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.user import User
    from src.domain.entities.workout import WorkoutTemplate


class TrainingPlanStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class TrainingPlan(Base):
    """
    Месячный (или произвольный) план пользователя.
    """

    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[TrainingPlanStatus] = mapped_column(
        Enum(TrainingPlanStatus, name="trainingplanstatus"),
        default=TrainingPlanStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="training_plans")
    scheduled_workouts: Mapped[list["ScheduledWorkout"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ScheduledWorkout.scheduled_for",
    )


class ScheduledWorkout(Base):
    """
    Конкретная тренировка в конкретный день (инстанс шаблона).
    """

    __tablename__ = "scheduled_workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        index=True,
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True, doc="0=Mon .. 6=Sun")
    volume_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped[TrainingPlan] = relationship(back_populates="scheduled_workouts")
    template: Mapped["WorkoutTemplate | None"] = relationship(back_populates="scheduled_workouts")

