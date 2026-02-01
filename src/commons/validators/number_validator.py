from __future__ import annotations

from src.commons.validators.base import BaseValidator
from src.commons.validators.contexts import NumberContext
from src.commons.validators.result import ValidationResult


class IntValidator(BaseValidator[NumberContext]):
    def validate(self, text: str, ctx: NumberContext) -> ValidationResult:
        try:
            value = int(text.strip())
        except ValueError:
            return ValidationResult.failure(ctx.error_invalid, code=ctx.error_code_invalid)
        if ctx.min_value is not None and value < int(ctx.min_value):
            return ValidationResult.failure(
                ctx.error_range or ctx.error_invalid,
                code=ctx.error_code_range or ctx.error_code_invalid,
            )
        if ctx.max_value is not None and value > int(ctx.max_value):
            return ValidationResult.failure(
                ctx.error_range or ctx.error_invalid,
                code=ctx.error_code_range or ctx.error_code_invalid,
            )
        return ValidationResult.success(value)


class FloatValidator(BaseValidator[NumberContext]):
    def validate(self, text: str, ctx: NumberContext) -> ValidationResult:
        try:
            value = float(text.strip())
        except ValueError:
            return ValidationResult.failure(ctx.error_invalid, code=ctx.error_code_invalid)
        if ctx.min_value is not None and value < ctx.min_value:
            return ValidationResult.failure(
                ctx.error_range or ctx.error_invalid,
                code=ctx.error_code_range or ctx.error_code_invalid,
            )
        if ctx.max_value is not None and value > ctx.max_value:
            return ValidationResult.failure(
                ctx.error_range or ctx.error_invalid,
                code=ctx.error_code_range or ctx.error_code_invalid,
            )
        return ValidationResult.success(value)
