from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class TextContext:
    max_length: int | None = None
    pattern: str | None = None
    error_max_length: str | None = None
    error_invalid: str = "Некорректное значение."
    error_code_invalid: str | None = None
    error_code_max_length: str | None = None


@dataclass(slots=True)
class NumberContext:
    min_value: float | None = None
    max_value: float | None = None
    error_invalid: str = "Введите число."
    error_range: str | None = None
    error_code_invalid: str | None = None
    error_code_range: str | None = None


@dataclass(slots=True)
class BoolContext:
    true_values: set[str] | None = None
    false_values: set[str] | None = None
    error_invalid: str = "Некорректное значение."
    error_code_invalid: str | None = None


@dataclass(slots=True)
class ChoiceContext:
    value_map: Mapping[str, str]
    error_choice: str = "Выберите вариант из списка."
    error_code_choice: str | None = None
