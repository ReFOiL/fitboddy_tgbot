from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base
from src.domain.value_objects.workout_profile import EquipmentName

if TYPE_CHECKING:
    from src.domain.entities.contraindication import Contraindication
    from src.domain.entities.muscle import Muscle

exercise_muscles = Table(
    "exercise_muscles",
    Base.metadata,
    Column("exercise_id", ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("muscle_id", ForeignKey("muscles.id", ondelete="CASCADE"), primary_key=True),
)
exercise_contraindications = Table(
    "exercise_contraindications",
    Base.metadata,
    Column("exercise_id", ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("contraindication_id", ForeignKey("contraindications.id", ondelete="CASCADE"), primary_key=True),
)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    equipment: Mapped[EquipmentName | None] = mapped_column(
        SqlEnum(
            EquipmentName,
            name="equipment_name",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    is_cardio: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    workout_category: Mapped[str] = mapped_column(
        String(50),
        default="full_body",
        doc="Группировка для планировщика: full_body | upper | lower | cardio",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    muscles: Mapped[list[Muscle]] = relationship(
        "Muscle",
        secondary=exercise_muscles,
        back_populates="exercises",
        lazy="selectin",
    )
    contraindications: Mapped[list[Contraindication]] = relationship(
        "Contraindication",
        secondary=exercise_contraindications,
        back_populates="exercises",
        lazy="selectin",
    )
