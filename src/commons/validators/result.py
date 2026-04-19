from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    value: str | int | float | bool | None = None
    error: str | None = None
    code: str | None = None


    @classmethod
    def success(cls, value: str | int | float | bool | None) -> "ValidationResult":
        return cls(ok=True, value=value, error=None, code=None)

    @classmethod
    def failure(cls, error: str, code: str | None = None) -> "ValidationResult":
        return cls(ok=False, value=None, error=error, code=code)
