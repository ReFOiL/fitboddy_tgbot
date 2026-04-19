from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Table, Column, UniqueConstraint, func
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
    """
    Вопросы анкеты (системные и кастомные).
    
    Системные вопросы (is_system=True):
    - system:goal, system:level, system:gender, system:equipment и т.д.
    - Используются для фильтрации и матчинга тренировок
    - Не могут быть удалены через админку
    
    Кастомные вопросы (is_system=False):
    - Создаются через админку
    - Используются для дополнительного скоринга
    - Могут быть привязаны к шаблонам через question_template_links
    """

    __tablename__ = "custom_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    text: Mapped[str] = mapped_column(String(500))
    answer_type: Mapped[AnswerType] = mapped_column(Enum(AnswerType, name="custom_answer_type"), index=True)
    min_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # Флаг системного вопроса
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Составной индекс для частых запросов: активные вопросы по порядку
        Index("idx_custom_question_active_order", "is_active", "order"),
        # Составной индекс для системных вопросов (часто используются в матчинге)
        Index("idx_custom_question_system_active", "is_system", "is_active"),
        # CHECK: min_value <= max_value если оба указаны
        CheckConstraint(
            "(min_value IS NULL) OR (max_value IS NULL) OR (min_value <= max_value)",
            name="ck_custom_question_value_range",
        ),
        # CHECK: order >= 0
        CheckConstraint(
            '"order" >= 0',
            name="ck_custom_question_order_positive",
        ),
        # CHECK: системные вопросы должны иметь ключ, начинающийся с "system:"
        CheckConstraint(
            "(is_system = false) OR (key LIKE 'system:%')",
            name="ck_custom_question_system_key",
        ),
    )

    options: Mapped[list[CustomQuestionOption]] = relationship(
        back_populates="question",
        order_by="CustomQuestionOption.sort_order",
        cascade="all, delete-orphan",
    )
    workout_templates: Mapped[list[WorkoutTemplate]] = relationship(
        secondary="question_template_links",
        back_populates="linked_questions",
    )
    scoring_weights: Mapped[list[CustomQuestionScoringWeight]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
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

    __table_args__ = (
        # Уникальность: одна опция с таким value для вопроса
        UniqueConstraint("question_id", "value", name="uq_question_option_value"),
        # CHECK: sort_order >= 0
        CheckConstraint(
            "sort_order >= 0",
            name="ck_custom_question_option_sort_positive",
        ),
    )


class CustomQuestionScoringWeight(Base):
    """
    Веса для ответов на кастомные вопросы при скоринге тренировок.
    
    Использует option_id для CHOICE вопросов (более эффективно чем строковый поиск).
    Для TEXT/NUMBER/BOOLEAN вопросов используется answer_value как fallback.
    """

    __tablename__ = "custom_question_scoring_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("custom_questions.id", ondelete="CASCADE"),
        index=True,
    )
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("custom_question_options.id", ondelete="CASCADE"),
        nullable=True,
        index=True,  # Индекс для быстрого поиска по option_id
    )
    answer_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,  # Fallback для TEXT/NUMBER/BOOLEAN вопросов
    )
    weight: Mapped[int] = mapped_column(Integer)  # положительное или отрицательное число
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    question: Mapped[CustomQuestion] = relationship(back_populates="scoring_weights")
    option: Mapped[CustomQuestionOption | None] = relationship()

    __table_args__ = (
        # Уникальность: один вес для опции вопроса ИЛИ для строкового значения
        UniqueConstraint("question_id", "option_id", name="uq_question_option_weight"),
        UniqueConstraint("question_id", "answer_value", name="uq_question_answer_value_weight"),
        # Составной индекс для быстрого поиска веса по вопросу и опции
        Index("idx_scoring_weight_question_option", "question_id", "option_id"),
        # Составной индекс для быстрого поиска веса по вопросу и строковому значению
        Index("idx_scoring_weight_question_answer", "question_id", "answer_value"),
        # CHECK: либо option_id, либо answer_value должен быть заполнен
        CheckConstraint(
            "(option_id IS NOT NULL) OR (answer_value IS NOT NULL)",
            name="ck_scoring_weight_has_value",
        ),
    )


from src.domain.entities.workout import WorkoutTemplate  # noqa: E402  # isort:skip
