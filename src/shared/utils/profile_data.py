from __future__ import annotations

from typing import Mapping, Sequence


def _find_item(items: Sequence[Mapping[str, object]], key: str) -> Mapping[str, object] | None:
    for item in items:
        if str(item.get("key", "")) == key:
            return item
    return None


def get_value(items: Sequence[Mapping[str, object]], key: str) -> object | None:
    item = _find_item(items, key)
    if item is None:
        return None
    return item.get("value")


def get_str(items: Sequence[Mapping[str, object]], key: str) -> str | None:
    value = get_value(items, key)
    return value if isinstance(value, str) else None


def get_int(items: Sequence[Mapping[str, object]], key: str) -> int | None:
    value = get_value(items, key)
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None


def get_float(items: Sequence[Mapping[str, object]], key: str) -> float | None:
    value = get_value(items, key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def get_str_list(items: Sequence[Mapping[str, object]], key: str) -> list[str] | None:
    value = get_value(items, key)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return None
