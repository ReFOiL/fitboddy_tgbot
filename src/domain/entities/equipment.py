from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.user import User


class Equipment(Base):
    """Справочник оборудования для тренировок."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # dumbbells, barbell, ...
    display_name: Mapped[str] = mapped_column(String(100))  # Гантели, Штанга, ...
    category: Mapped[str] = mapped_column(String(50))  # free_weights, machines, cardio, bodyweight
    is_home_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Примечание: связь с User удалена - данные об оборудовании пользователя хранятся в UserAnswer
