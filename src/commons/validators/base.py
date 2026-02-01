from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.commons.validators.result import ValidationResult

C = TypeVar("C")


class BaseValidator(Generic[C], ABC):
    @abstractmethod
    def validate(self, text: str, ctx: C) -> ValidationResult:  # pragma: no cover - abstract base
        raise NotImplementedError
