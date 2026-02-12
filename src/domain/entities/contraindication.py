"""Справочник противопоказаний (админ может редактировать)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from src.domain.entities.base import Base

if TYPE_CHECKING:
    from src.domain.entities.exercise import Exercise


class Contraindication(Base):
    __tablename__ = "contraindications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default=expression.text("0"), default=0)

    exercises: Mapped[list["Exercise"]] = relationship(
        "Exercise",
        secondary="exercise_contraindications",
        back_populates="contraindications",
    )
