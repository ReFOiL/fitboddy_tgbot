from __future__ import annotations

from src.commons.validators import ValidationResult
from src.domain.questionnaire.errors import ValidationErrorCode, get_error_message
from src.domain.questionnaire.models import Question
from src.domain.questionnaire.pipeline import AnswerValidationPipeline
from src.domain.questionnaire.registry import AnswerTypeRegistry


class AnswerValidator:
    def __init__(
        self,
        registry: AnswerTypeRegistry | None = None,
        pipeline: AnswerValidationPipeline | None = None,
    ) -> None:
        self._registry = registry or AnswerTypeRegistry()
        self._pipeline = pipeline or AnswerValidationPipeline()

    def validate(
        self,
        question: Question,
        text: str,
    ) -> tuple[str | int | bool | list[str] | None, str | None]:
        text_raw = text.strip()
        early = self._pipeline.validate(question, text_raw)
        if early is not None:
            return _normalize_result(early)
        return _normalize_result(self._registry.validate(question, text_raw))


def _normalize_result(
    result: ValidationResult,
) -> tuple[str | int | bool | list[str] | None, str | None]:
    if not result.ok:
        return None, result.error
    value = result.value
    if value is None:
        return None, None
    if isinstance(value, (str, int, bool)):
        return value, None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value, None
    return None, get_error_message(ValidationErrorCode.INVALID)
