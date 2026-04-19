from __future__ import annotations

from src.domain.entities.questionnaire import CustomQuestion
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.question_schemas import (
    CustomQuestionCreate,
    CustomQuestionOut,
    CustomQuestionUpdate,
    OptionItem,
)


class OptionsNormalizer:
    def normalize(
        self,
        options: list[OptionItem] | None,
    ) -> list[dict[str, str]] | None:
        if options is None:
            return None
        return [item.model_dump() for item in options]


class QuestionPayloadBuilder(BaseController):
    def __init__(self, normalizer: OptionsNormalizer) -> None:
        super().__init__()
        self._normalizer = normalizer

    def build_create(self, data: CustomQuestionCreate) -> ControllerResult[dict[str, str | int | float | bool | None | list[dict[str, str]]]]:
        key_result = self._ensure_key(data.key)
        if not key_result.ok:
            return key_result
        payload = data.model_dump()
        payload["key"] = key_result.data
        payload["options"] = self._normalizer.normalize(data.options)
        return self.ok(payload)

    def build_update(self, data: CustomQuestionUpdate) -> ControllerResult[dict[str, str | int | float | bool | None | list[dict[str, str]]]]:
        updates = data.model_dump(exclude_unset=True)
        if "key" in updates:
            key_result = self._ensure_key(updates["key"])
            if not key_result.ok:
                return key_result
            updates["key"] = key_result.data
        if "options" in updates:
            updates["options"] = self._normalizer.normalize(data.options)
        return self.ok(updates)

    def _ensure_key(self, value: str | None) -> ControllerResult[str]:
        if value is None or not value.strip():
            return self.bad_request("Question key is required")
        return self.ok(value.strip())


class QuestionPresenter:
    def to_out(self, question: CustomQuestion) -> CustomQuestionOut:
        is_system = bool(question.is_system or (question.key or "").startswith("system:"))
        return CustomQuestionOut(
            id=question.id,
            key=question.key,
            order=question.order,
            text=question.text,
            answer_type=question.answer_type,
            options=[{"value": opt.value, "label": opt.label} for opt in question.options],
            min_value=question.min_value,
            max_value=question.max_value,
            pattern=question.pattern,
            is_required=question.is_required,
            is_active=question.is_active,
            is_system=is_system,
            category=question.category,
            tags=question.tags,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )
