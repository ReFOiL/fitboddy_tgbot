from __future__ import annotations

from typing import Protocol

from src.commons.validators import ValidationResult
from src.domain.questionnaire.models import Question


class AnswerValidationStep(Protocol):
    def run(self, question: Question, text: str) -> ValidationResult | None:
        raise NotImplementedError


class AnswerTypeStrategy(Protocol):
    def validate(self, question: Question, text: str) -> ValidationResult:
        raise NotImplementedError
