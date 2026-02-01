from __future__ import annotations

from src.commons.validators.base import BaseValidator
from src.commons.validators.contexts import ChoiceContext
from src.commons.validators.list_parser import CommaListParser
from src.commons.validators.result import ValidationResult


class SingleChoiceValidator(BaseValidator[ChoiceContext]):
    def validate(self, text: str, ctx: ChoiceContext) -> ValidationResult:
        key = text.strip().lower()
        value = ctx.value_map.get(key)
        if value is None:
            return ValidationResult.failure(ctx.error_choice, code=ctx.error_code_choice)
        return ValidationResult.success(value)


class MultiChoiceValidator(BaseValidator[ChoiceContext]):
    def __init__(self, parser: CommaListParser | None = None) -> None:
        self._parser = parser or CommaListParser()

    def validate(self, text: str, ctx: ChoiceContext) -> ValidationResult:
        items = self._parser.parse(text)
        if not items:
            return ValidationResult.success([])
        values: list[str] = []
        for item in items:
            value = ctx.value_map.get(item.strip().lower())
            if value is None:
                return ValidationResult.failure(ctx.error_choice, code=ctx.error_code_choice)
            values.append(value)
        return ValidationResult.success(values)
