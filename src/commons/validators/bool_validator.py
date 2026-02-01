from __future__ import annotations

from src.commons.validators.base import BaseValidator
from src.commons.validators.contexts import BoolContext
from src.commons.validators.result import ValidationResult


class BoolValidator(BaseValidator[BoolContext]):
    def validate(self, text: str, ctx: BoolContext) -> ValidationResult:
        text_norm = text.strip().lower()
        true_values = ctx.true_values or {"да", "yes", "true", "1"}
        false_values = ctx.false_values or {"нет", "no", "false", "0"}
        if text_norm in true_values:
            return ValidationResult.success(True)
        if text_norm in false_values:
            return ValidationResult.success(False)
        return ValidationResult.failure(ctx.error_invalid, code=ctx.error_code_invalid)
