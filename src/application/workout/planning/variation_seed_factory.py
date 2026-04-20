from __future__ import annotations

import zlib

from src.application.workout.planning.models import VariationSeedRequest


class PlanVariationSeedFactory:
    def build_seed(self, request: VariationSeedRequest) -> int:
        ids_part = ",".join(str(e.id) for e in sorted(request.exercises, key=lambda x: x.id))
        blob = (
            f"{request.user_id}\n"
            f"{request.anchor.isoformat()}\n"
            f"{request.workouts_per_week}\n"
            f"{request.goal}\n"
            f"{ids_part}"
        ).encode()
        return zlib.crc32(blob) & 0xFFFFFFFF
