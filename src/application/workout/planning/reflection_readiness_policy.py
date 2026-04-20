from __future__ import annotations

from src.domain.value_objects.workout_profile import ReflectionEnergy


class ReflectionReadinessPolicy:
    """Преобразует историю энергии в множитель готовности к нагрузке."""

    def readiness_multiplier(self, energies: list[ReflectionEnergy]) -> float:
        if not energies:
            return 1.0
        mapping = {
            ReflectionEnergy.LOW: -0.2,
            ReflectionEnergy.OK: 0.0,
            ReflectionEnergy.HIGH: 0.1,
        }
        scored = [mapping.get(item, 0.0) for item in energies]
        avg = sum(scored) / len(scored)
        return max(0.8, min(1.1, round(1.0 + avg, 3)))

