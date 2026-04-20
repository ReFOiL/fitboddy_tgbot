from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.workout_profile import TrainingGoal, TrainingLevel


@dataclass(frozen=True, slots=True)
class PlanPhase:
    name: str
    weekly_volume_by_week: dict[int, float]


class GoalPhaseProgressionPolicy:
    def resolve_phase(
        self,
        *,
        cycle_index: int,
        goal: TrainingGoal,
        level: TrainingLevel,
    ) -> PlanPhase:
        if goal == TrainingGoal.REHABILITATION:
            return PlanPhase(name="recovery", weekly_volume_by_week={1: 0.8, 2: 0.85, 3: 0.9, 4: 0.85})

        ring = ("accumulation", "intensification", "deload")
        phase_name = ring[(max(cycle_index, 1) - 1) % len(ring)]
        if phase_name == "accumulation":
            return PlanPhase(name=phase_name, weekly_volume_by_week={1: 0.95, 2: 1.05, 3: 1.12, 4: 1.0})
        if phase_name == "intensification":
            base = {1: 1.0, 2: 1.1, 3: 1.22, 4: 1.08}
            if level == TrainingLevel.ADVANCED:
                base = {1: 1.05, 2: 1.16, 3: 1.28, 4: 1.12}
            return PlanPhase(name=phase_name, weekly_volume_by_week=base)
        return PlanPhase(name=phase_name, weekly_volume_by_week={1: 0.86, 2: 0.9, 3: 0.95, 4: 0.82})

