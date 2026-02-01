from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base
from src.domain.value_objects.questionnaire import AnswerType


question_template_links = Table(
    "question_template_links",
    Base.metadata,
    Column("question_id", ForeignKey("custom_questions.id", ondelete="CASCADE"), primary_key=True),
    Column("template_id", ForeignKey("workout_templates.id", ondelete="CASCADE"), primary_key=True),
)


class CustomQuestion(Base):
    __tablename__ = "custom_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    text: Mapped[str] = mapped_column(String(500))
    answer_type: Mapped[AnswerType] = mapped_column(Enum(AnswerType, name="custom_answer_type"))
    min_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    options: Mapped[list["CustomQuestionOption"]] = relationship(
        back_populates="question",
        order_by="CustomQuestionOption.sort_order",
        cascade="all, delete-orphan",
    )
    workout_templates: Mapped[list["WorkoutTemplate"]] = relationship(
        secondary="question_template_links",
        back_populates="linked_questions",
    )


class CustomQuestionOption(Base):
    __tablename__ = "custom_question_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("custom_questions.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    question: Mapped[CustomQuestion] = relationship(back_populates="options")


from src.domain.entities.workout import WorkoutTemplate  # noqa: E402  # isort:skip
