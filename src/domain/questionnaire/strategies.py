from __future__ import annotations

from src.commons.validators import (
    BoolContext,
    BoolValidator,
    ChoiceContext,
    IntValidator,
    MultiChoiceValidator,
    NumberContext,
    SingleChoiceValidator,
    TextContext,
    TextValidator,
    ValidationResult,
)
from src.domain.questionnaire.errors import ValidationErrorCode, get_error_message
from src.domain.questionnaire.interfaces import AnswerTypeStrategy
from src.domain.questionnaire.models import Question
from src.domain.questionnaire.utils import build_choice_map


class TextAnswerStrategy(AnswerTypeStrategy):
    def __init__(self, validator: TextValidator | None = None) -> None:
        self._validator = validator or TextValidator()

    def validate(self, question: Question, text: str) -> ValidationResult:
        return self._validator.validate(
            text,
            TextContext(
                max_length=200,
                pattern=question.pattern,
                error_invalid=get_error_message(ValidationErrorCode.FORMAT_INVALID),
                error_code_invalid=ValidationErrorCode.FORMAT_INVALID.value,
                error_max_length=get_error_message(ValidationErrorCode.MAX_LENGTH),
                error_code_max_length=ValidationErrorCode.MAX_LENGTH.value,
            ),
        )


class NumberAnswerStrategy(AnswerTypeStrategy):
    def __init__(self, validator: IntValidator | None = None) -> None:
        self._validator = validator or IntValidator()

    def validate(self, question: Question, text: str) -> ValidationResult:
        return self._validator.validate(
            text,
            NumberContext(
                min_value=question.min_value,
                max_value=question.max_value,
                error_invalid=get_error_message(ValidationErrorCode.NUMBER_INVALID),
                error_code_invalid=ValidationErrorCode.NUMBER_INVALID.value,
                error_range=get_error_message(ValidationErrorCode.NUMBER_RANGE),
                error_code_range=ValidationErrorCode.NUMBER_RANGE.value,
            ),
        )


class BooleanAnswerStrategy(AnswerTypeStrategy):
    def __init__(self, validator: BoolValidator | None = None) -> None:
        self._validator = validator or BoolValidator()

    def validate(self, question: Question, text: str) -> ValidationResult:
        return self._validator.validate(
            text,
            BoolContext(
                error_invalid=get_error_message(ValidationErrorCode.BOOLEAN_INVALID),
                error_code_invalid=ValidationErrorCode.BOOLEAN_INVALID.value,
            ),
        )


class SingleChoiceAnswerStrategy(AnswerTypeStrategy):
    def __init__(self, validator: SingleChoiceValidator | None = None) -> None:
        self._validator = validator or SingleChoiceValidator()

    def validate(self, question: Question, text: str) -> ValidationResult:
        if not question.options:
            return ValidationResult.failure(
                get_error_message(ValidationErrorCode.OPTIONS_NOT_CONFIGURED),
                code=ValidationErrorCode.OPTIONS_NOT_CONFIGURED.value,
            )
        return self._validator.validate(
            text,
            ChoiceContext(
                value_map=build_choice_map(question.options),
                error_choice=get_error_message(ValidationErrorCode.CHOICE_INVALID),
                error_code_choice=ValidationErrorCode.CHOICE_INVALID.value,
            ),
        )


class MultiChoiceAnswerStrategy(AnswerTypeStrategy):
    def __init__(self, validator: MultiChoiceValidator | None = None) -> None:
        self._validator = validator or MultiChoiceValidator()

    def validate(self, question: Question, text: str) -> ValidationResult:
        if not question.options:
            return ValidationResult.failure(
                get_error_message(ValidationErrorCode.OPTIONS_NOT_CONFIGURED),
                code=ValidationErrorCode.OPTIONS_NOT_CONFIGURED.value,
            )
        result = self._validator.validate(
            text,
            ChoiceContext(
                value_map=build_choice_map(question.options),
                error_choice=get_error_message(ValidationErrorCode.CHOICE_INVALID),
                error_code_choice=ValidationErrorCode.CHOICE_INVALID.value,
            ),
        )
        if result.ok and question.is_required and not result.value:
            return ValidationResult.failure(
                get_error_message(ValidationErrorCode.CHOICE_REQUIRED),
                code=ValidationErrorCode.CHOICE_REQUIRED.value,
            )
        return result
