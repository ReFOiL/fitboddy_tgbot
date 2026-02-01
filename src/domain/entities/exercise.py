from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    equipment: Mapped[str | None] = mapped_column(String(64))
    is_cardio: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    contraindications: Mapped[list[str]] = mapped_column(
        String(512), default="", doc="Comma-separated list"
    )

    workout_templates: Mapped[list["WorkoutTemplate"]] = relationship(
        back_populates="exercises", secondary="workout_exercises"
    )


from src.domain.entities.workout import WorkoutTemplate  # noqa: E402  # isort:skip

