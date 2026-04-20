from __future__ import annotations

from src.domain.value_objects.workout_profile import PerceivedEffort


class WorkoutCallbackPayloadParser:
    @staticmethod
    def int_after_prefix(raw: str | None, prefix: str) -> int | None:
        if not raw or not raw.startswith(prefix):
            return None
        try:
            return int(raw.split(":", 1)[1])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def effort(raw: str | None) -> tuple[PerceivedEffort, int] | None:
        if not raw:
            return None
        parts = raw.split(":")
        if len(parts) != 3 or parts[0] != "effort":
            return None
        level = PerceivedEffort.from_raw(parts[1])
        if level is None:
            return None
        try:
            scheduled_id = int(parts[2])
        except ValueError:
            return None
        return level, scheduled_id
