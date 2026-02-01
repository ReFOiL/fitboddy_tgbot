from __future__ import annotations

from typing import Sequence

from src.commons.validators import ValidationResult
from src.domain.questionnaire.errors import ValidationErrorCode, get_error_message
from src.domain.questionnaire.interfaces import AnswerValidationStep
from src.domain.questionnaire.models import Question


class RequiredAnswerStep:
    def run(self, question: Question, text: str) -> ValidationResult | None:
        if not text.strip() and question.is_required:
            return ValidationResult.failure(
                get_error_message(ValidationErrorCode.REQUIRED),
                code=ValidationErrorCode.REQUIRED.value,
            )
        return None


class OptionalSkipStep:
    def run(self, question: Question, text: str) -> ValidationResult | None:
        text_raw = text.strip()
        if not question.is_required and not text_raw:
            return ValidationResult.success(None)
        if not question.is_required and text_raw.lower() in {"пропустить", "skip"}:
            return ValidationResult.success(None)
        return None


class AnswerValidationPipeline:
    def __init__(self, steps: Sequence[AnswerValidationStep] | None = None) -> None:
        self._steps = list(steps or [RequiredAnswerStep(), OptionalSkipStep()])

    def validate(self, question: Question, text: str) -> ValidationResult | None:
        for step in self._steps:
            result = step.run(question, text)
            if result is not None:
                return result
        return None
