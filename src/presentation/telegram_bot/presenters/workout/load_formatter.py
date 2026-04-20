from __future__ import annotations


class WorkoutLoadFormatter:
    @staticmethod
    def scale_int(value: int | None, multiplier: float) -> int | None:
        if value is None:
            return None
        return max(1, int(round(value * multiplier)))

    @classmethod
    def format_volume_part(
        cls,
        *,
        sets: int | None,
        reps: int | None,
        duration_seconds: int | None,
        multiplier: float,
    ) -> str:
        scaled_sets = cls.scale_int(sets, multiplier)
        scaled_reps = cls.scale_int(reps, multiplier)
        if scaled_sets and scaled_reps:
            return f"{scaled_sets}×{scaled_reps}"
        if duration_seconds:
            scaled_duration = cls.scale_int(duration_seconds, multiplier) or duration_seconds
            return f"{scaled_duration} сек"
        return ""
