"""Грубые зоны для восстановления между тренировками (не путать со строками-мишцами в каталоге)."""
from __future__ import annotations

import enum


class CoarseMuscleGroup(str, enum.Enum):
    """Фиксированный набор зон из продуктового ТЗ (планировщик, 48 ч)."""

    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    CARDIO = "cardio"
