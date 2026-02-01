from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("custom_questions.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("custom_question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    value: Mapped[str | int | bool | None] = mapped_column(JSON, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="answers")
    question: Mapped["CustomQuestion"] = relationship()
    option: Mapped["CustomQuestionOption | None"] = relationship()

    __table_args__ = (
        Index("idx_user_answers_composite", "user_id", "question_id", "option_id", unique=True),
    )


from src.domain.entities.user import User  # noqa: E402  # isort:skip
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption  # noqa: E402  # isort:skip
