from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.base import Base


class UserAnswer(Base):
    """
    Ответы пользователя на вопросы анкеты.
    
    Поддерживает:
    - SINGLE_CHOICE: один ответ с option_id
    - MULTIPLE_CHOICE: несколько ответов с разными option_id (один UserAnswer на каждую опцию)
    - TEXT/NUMBER/BOOLEAN: один ответ с value
    """

    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("custom_questions.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("custom_question_options.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    value: Mapped[str | int | bool | None] = mapped_column(JSON, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="answers")
    question: Mapped[CustomQuestion] = relationship()
    option: Mapped[CustomQuestionOption | None] = relationship()

    __table_args__ = (
        # Уникальность: один ответ пользователя на вопрос с конкретной опцией
        # Для MULTIPLE_CHOICE может быть несколько записей с разными option_id
        UniqueConstraint("user_id", "question_id", "option_id", name="uq_user_question_option"),
        # Индекс для быстрого поиска всех ответов пользователя
        Index("idx_user_answers_user_question", "user_id", "question_id"),
        # Составной индекс для поиска системных ответов пользователя (часто используется в матчинге)
        # Используется через JOIN с CustomQuestion WHERE is_system = true
        Index("idx_user_answers_user_id", "user_id"),
        # CHECK: либо option_id, либо value должен быть заполнен
        CheckConstraint(
            "(option_id IS NOT NULL) OR (value IS NOT NULL)",
            name="ck_user_answer_has_value",
        ),
    )


from src.domain.entities.user import User  # noqa: E402  # isort:skip
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption  # noqa: E402  # isort:skip
