from __future__ import annotations

from typing import Mapping

from src.commons.validators import ValidationResult
from src.domain.questionnaire.errors import ValidationErrorCode, get_error_message
from src.domain.questionnaire.interfaces import AnswerTypeStrategy
from src.domain.questionnaire.models import Question
from src.domain.questionnaire.strategies import (
    BooleanAnswerStrategy,
    MultiChoiceAnswerStrategy,
    NumberAnswerStrategy,
    SingleChoiceAnswerStrategy,
    TextAnswerStrategy,
)
from src.domain.value_objects.questionnaire import AnswerType


class AnswerTypeRegistry:
    def __init__(self, strategies: Mapping[AnswerType, AnswerTypeStrategy] | None = None) -> None:
        if strategies is None:
            strategies = {
                AnswerType.TEXT: TextAnswerStrategy(),
                AnswerType.NUMBER: NumberAnswerStrategy(),
                AnswerType.BOOLEAN: BooleanAnswerStrategy(),
                AnswerType.SINGLE_CHOICE: SingleChoiceAnswerStrategy(),
                AnswerType.MULTIPLE_CHOICE: MultiChoiceAnswerStrategy(),
            }
        self._strategies = dict(strategies)

    def validate(self, question: Question, text: str) -> ValidationResult:
        strategy = self._strategies.get(question.answer_type)
        if strategy is None:
            return ValidationResult.failure(
                get_error_message(ValidationErrorCode.ANSWER_TYPE_INVALID),
                code=ValidationErrorCode.ANSWER_TYPE_INVALID.value,
            )
        return strategy.validate(question, text)
