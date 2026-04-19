from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class Tariff(enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    tariff: Mapped[Tariff] = mapped_column(Enum(Tariff), default=Tariff.FREE)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    has_completed_profile: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cached_tdee: Mapped[float | None] = mapped_column(Float, nullable=True)
    cached_bmi: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Все данные профиля (gender, equipment, goal, level и т.д.) хранятся в UserAnswer
    # Это единственный источник истины - никакой денормализации!

    training_plans: Mapped[list[TrainingPlan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list[UserAnswer]] = relationship(
        cascade="all, delete-orphan",
        back_populates="user",
    )


from src.domain.entities.training_plan import TrainingPlan  # noqa: E402  # isort:skip
from src.domain.entities.user_answer import UserAnswer  # noqa: E402  # isort:skip

