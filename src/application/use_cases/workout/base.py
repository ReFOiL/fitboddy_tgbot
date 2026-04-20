from __future__ import annotations

from time import perf_counter
from typing import Awaitable, Callable, TypeVar

import structlog

from src.application.services.metrics import (
    workout_use_case_duration_seconds,
    workout_use_case_failures_total,
    workout_use_case_runs_total,
)

logger = structlog.get_logger()

ResultT = TypeVar("ResultT")


class WorkoutUseCaseMetrics:
    async def run_with_metrics(
        self,
        use_case_name: str,
        operation: Callable[[], Awaitable[ResultT]],
    ) -> ResultT:
        metric_prefix = use_case_name.strip().lower().replace(" ", "_")
        started_at = perf_counter()
        workout_use_case_runs_total.labels(use_case=metric_prefix).inc()
        try:
            return await operation()
        except Exception:
            workout_use_case_failures_total.labels(use_case=metric_prefix).inc()
            logger.exception("workout.use_case_failed", use_case=metric_prefix)
            raise
        finally:
            elapsed = perf_counter() - started_at
            workout_use_case_duration_seconds.labels(use_case=metric_prefix).observe(elapsed)
