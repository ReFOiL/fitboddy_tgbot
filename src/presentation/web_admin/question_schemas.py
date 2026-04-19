from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.value_objects.questionnaire import AnswerType


class OptionItem(BaseModel):
    value: str
    label: str


class CustomQuestionCreate(BaseModel):
    key: str
    order: int = 0
    text: str = Field(..., max_length=500)
    answer_type: AnswerType
    options: list[OptionItem] | None = None
    min_value: int | None = None
    max_value: int | None = None
    pattern: str | None = None
    is_required: bool = False
    is_active: bool = True
    category: str | None = Field(default=None, max_length=50)
    tags: list[str] = Field(default_factory=list)


class CustomQuestionUpdate(BaseModel):
    key: str | None = None
    order: int | None = None
    text: str | None = Field(default=None, max_length=500)
    answer_type: AnswerType | None = None
    options: list[OptionItem] | None = None
    min_value: int | None = None
    max_value: int | None = None
    pattern: str | None = None
    is_required: bool | None = None
    is_active: bool | None = None
    category: str | None = Field(default=None, max_length=50)
    tags: list[str] | None = None


class CustomQuestionOut(BaseModel):
    id: int
    key: str
    order: int
    text: str
    answer_type: AnswerType
    options: list[dict[str, str]] | None = None
    min_value: int | None = None
    max_value: int | None = None
    pattern: str | None = None
    is_required: bool
    is_active: bool
    is_system: bool
    category: str | None = None
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class QuestionOrderUpdate(BaseModel):
    new_order: int


class MessageOut(BaseModel):
    message: str


class QuestionCreatedOut(MessageOut):
    id: int


# --- Scoring Weights ---
class ScoringWeightOut(BaseModel):
    id: int
    question_id: int
    answer_value: str
    weight: int
    created_at: datetime
    updated_at: datetime


class ScoringWeightCreate(BaseModel):
    answer_value: str = Field(..., max_length=255)
    weight: int = Field(..., description="Weight can be positive or negative")
