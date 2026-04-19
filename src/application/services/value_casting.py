from __future__ import annotations

from typing import Protocol


class ValueCasterProtocol(Protocol):
    def to_str(self, value: str | int | float | bool | None) -> str | None: ...
    def to_int(self, value: str | int | float | bool | None) -> int | None: ...
    def to_float(self, value: str | int | float | bool | None) -> float | None: ...


class LenientCaster(ValueCasterProtocol):
    def to_str(self, value: str | int | float | bool | None) -> str | None:
        return value if isinstance(value, str) else None

    def to_int(self, value: str | int | float | bool | None) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def to_float(self, value: str | int | float | bool | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None


class StrictCaster(ValueCasterProtocol):
    def to_str(self, value: str | int | float | bool | None) -> str | None:
        return value if isinstance(value, str) else None

    def to_int(self, value: str | int | float | bool | None) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def to_float(self, value: str | int | float | bool | None) -> float | None:
        if isinstance(value, bool):
            return None
        return float(value) if isinstance(value, (int, float)) else None
