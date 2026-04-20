from __future__ import annotations

from src.application.workout.planning.models import LoadScalingRequest


class LoadScalingPolicy:
    def scale(self, request: LoadScalingRequest) -> tuple[int | None, int | None, int | None]:
        if request.user_load <= 0 or abs(request.user_load - 1.0) < 1e-6:
            return request.sets, request.reps, request.duration_seconds
        new_sets = max(1, round(request.sets * request.user_load)) if request.sets is not None else None
        new_reps = max(1, round(request.reps * request.user_load)) if request.reps is not None else None
        new_duration = (
            max(10, round(request.duration_seconds * request.user_load))
            if request.duration_seconds is not None
            else None
        )
        return new_sets, new_reps, new_duration
