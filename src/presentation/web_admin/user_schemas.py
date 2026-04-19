from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    created_at: datetime
    has_completed_profile: bool
    profile_completed_at: datetime | None


class OptionOut(BaseModel):
    value: str
    label: str


class AnswerGroupOut(BaseModel):
    question_id: int
    question_key: str
    question_text: str
    answer_type: str
    options: list[OptionOut] | None = None
    value: str | int | bool | list[str] | None = None
    answered_at: datetime | None = None
    updated_at: datetime | None = None


class UserDetailOut(UserOut):
    answers: list[AnswerGroupOut]

