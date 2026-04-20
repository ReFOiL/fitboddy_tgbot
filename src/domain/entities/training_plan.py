from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base
from src.domain.value_objects.workout_profile import PerceivedEffort

if TYPE_CHECKING:
    from src.domain.entities.user import User


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
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[TrainingPlanStatus] = mapped_column(
        Enum(TrainingPlanStatus, name="trainingplanstatus"),
        default=TrainingPlanStatus.ACTIVE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_training_plan_user_status", "user_id", "status"),
        CheckConstraint(
            "start_date <= end_date",
            name="ck_training_plan_date_range",
        ),
    )

    user: Mapped[User] = relationship(back_populates="training_plans")
    scheduled_workouts: Mapped[list[ScheduledWorkout]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ScheduledWorkout.scheduled_for",
    )


class ScheduledWorkout(Base):
    """Конкретная тренировка в конкретный день (строки в `session_exercises`)."""

    __tablename__ = "scheduled_workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        index=True,
    )
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="0=Mon .. 6=Sun",
    )
    volume_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    perceived_effort: Mapped[PerceivedEffort | None] = mapped_column(
        String(16),
        nullable=True,
        doc="После тренировки: easy | ok | hard",
    )

    __table_args__ = (
        Index("idx_scheduled_workout_plan_date", "plan_id", "scheduled_for"),
        UniqueConstraint("plan_id", "scheduled_for", name="uq_scheduled_workout_plan_date"),
        CheckConstraint(
            "(day_of_week IS NULL) OR (day_of_week >= 0 AND day_of_week <= 6)",
            name="ck_scheduled_workout_day_of_week",
        ),
        CheckConstraint(
            "volume_multiplier > 0",
            name="ck_scheduled_workout_volume_positive",
        ),
        CheckConstraint(
            "(is_completed = false) OR (completed_at IS NOT NULL)",
            name="ck_scheduled_workout_completed",
        ),
    )

    plan: Mapped[TrainingPlan] = relationship(back_populates="scheduled_workouts")
    session_exercises: Mapped[list["ScheduledWorkoutExercise"]] = relationship(
        back_populates="scheduled_workout",
        cascade="all, delete-orphan",
        order_by="ScheduledWorkoutExercise.sort_order",
    )


class ScheduledWorkoutExercise(Base):
    """Снимок упражнений на конкретную дату."""

    __tablename__ = "scheduled_workout_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheduled_workout_id: Mapped[int] = mapped_column(
        ForeignKey("scheduled_workouts.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scheduled_workout: Mapped[ScheduledWorkout] = relationship(back_populates="session_exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise")


from src.domain.entities.exercise import Exercise  # noqa: E402  # isort:skip
