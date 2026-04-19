"""Защита контрактных вопросов с ключом system:* в админ-сервисе."""
from __future__ import annotations

import pytest

from src.application.services.custom_question_admin import CustomQuestionAdminService
from src.commons.exceptions import SystemQuestionMutationError
from src.domain.entities.questionnaire import CustomQuestion
from src.domain.value_objects.questionnaire import AnswerType


class FakeQuestionsRepo:
    def __init__(self, question: CustomQuestion | None) -> None:
        self._question = question

    async def get(self, question_id: int) -> CustomQuestion | None:
        if self._question is None:
            return None
        if self._question.id != question_id:
            return None
        return self._question


class FakeUOW:
    def __init__(self, question: CustomQuestion | None) -> None:
        self.custom_questions = FakeQuestionsRepo(question)

    async def __aenter__(self) -> FakeUOW:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        return None


def _system_goal() -> CustomQuestion:
    return CustomQuestion(
        id=1,
        key="system:goal",
        order=1,
        text="Цель",
        answer_type=AnswerType.SINGLE_CHOICE,
        is_required=True,
    )


def _custom_foo() -> CustomQuestion:
    return CustomQuestion(
        id=2,
        key="custom:foo",
        order=11,
        text="Кастом",
        answer_type=AnswerType.TEXT,
        is_required=False,
    )


def _custom_bar() -> CustomQuestion:
    return CustomQuestion(
        id=3,
        key="custom:bar",
        order=12,
        text="Бар",
        answer_type=AnswerType.TEXT,
        is_required=False,
    )


@pytest.mark.asyncio
async def test_create_rejects_system_key_prefix() -> None:
    service = CustomQuestionAdminService(FakeUOW(None))
    with pytest.raises(SystemQuestionMutationError, match="Создавать вопросы"):
        await service.create(
            {
                "key": "system:evil",
                "order": 1,
                "text": "X",
                "answer_type": AnswerType.TEXT,
                "is_required": False,
                "is_active": True,
                "category": None,
                "tags": [],
            }
        )


@pytest.mark.asyncio
async def test_deactivate_system_question_raises() -> None:
    question = _system_goal()
    service = CustomQuestionAdminService(FakeUOW(question))
    with pytest.raises(SystemQuestionMutationError, match="деактивировать"):
        await service.deactivate(1)


@pytest.mark.asyncio
async def test_deactivate_custom_question_sets_inactive() -> None:
    question = _custom_foo()
    service = CustomQuestionAdminService(FakeUOW(question))
    await service.deactivate(2)
    assert question.is_active is False


@pytest.mark.parametrize(
    ("updates", "match"),
    [
        pytest.param({"is_active": False}, "is_active", id="system-forbidden-is_active"),
    ],
)
@pytest.mark.asyncio
async def test_update_system_question_forbidden_fields_raise(updates: dict[str, object], match: str) -> None:
    q = _system_goal()
    service = CustomQuestionAdminService(FakeUOW(q))
    with pytest.raises(SystemQuestionMutationError, match=match):
        await service.update(1, updates)


@pytest.mark.asyncio
async def test_update_system_question_can_change_text() -> None:
    q = _system_goal()
    service = CustomQuestionAdminService(FakeUOW(q))
    await service.update(1, {"text": "Обновлённая формулировка"})
    assert q.text == "Обновлённая формулировка"


@pytest.mark.asyncio
async def test_update_custom_cannot_rename_key_to_system_prefix() -> None:
    q = _custom_bar()
    service = CustomQuestionAdminService(FakeUOW(q))
    with pytest.raises(SystemQuestionMutationError, match=r"system:\*"):
        await service.update(3, {"key": "system:stolen"})
