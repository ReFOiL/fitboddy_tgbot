from __future__ import annotations

import re

from src.commons.validators.base import BaseValidator
from src.commons.validators.contexts import TextContext
from src.commons.validators.result import ValidationResult


class TextValidator(BaseValidator[TextContext]):
    def validate(self, text: str, ctx: TextContext) -> ValidationResult:
        value = text.strip()
        if ctx.max_length is not None and len(value) > ctx.max_length:
            return ValidationResult.failure(
                ctx.error_max_length or f"Максимальная длина {ctx.max_length}.",
                code=ctx.error_code_max_length,
            )
        if ctx.pattern and not re.fullmatch(ctx.pattern, value):
            return ValidationResult.failure(ctx.error_invalid, code=ctx.error_code_invalid)
        return ValidationResult.success(value)
