from __future__ import annotations

from src.application.services.workout_analytics_admin import (
    WorkoutAnalyticsAdminService,
    WorkoutAnalyticsFilters,
)
from src.presentation.web_admin.admin_schemas import (
    WorkoutAnalyticsAlertOut,
    WorkoutAnalyticsSummaryOut,
    WorkoutCycleFunnelStepOut,
    WorkoutRetentionCohortOut,
)
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult


class WorkoutAnalyticsController(BaseController):
    def __init__(self, service: WorkoutAnalyticsAdminService) -> None:
        super().__init__()
        self._service = service

    async def get_summary(
        self,
        *,
        goal: str | None = None,
        level: str | None = None,
        workout_location: str | None = None,
        equipment: str | None = None,
    ) -> ControllerResult[WorkoutAnalyticsSummaryOut]:
        summary = await self._service.get_summary(
            WorkoutAnalyticsFilters(
                goal=(goal or "").strip().lower() or None,
                level=(level or "").strip().lower() or None,
                workout_location=(workout_location or "").strip().lower() or None,
                equipment=(equipment or "").strip().lower() or None,
            )
        )
        return self.ok(
            WorkoutAnalyticsSummaryOut(
                users_total=summary.users_total,
                users_with_profile=summary.users_with_profile,
                users_with_2_cycles=summary.users_with_2_cycles,
                d7_retention_rate=summary.d7_retention_rate,
                d30_retention_rate=summary.d30_retention_rate,
                avg_cycle_completion_rate=summary.avg_cycle_completion_rate,
                avg_adherence_score=summary.avg_adherence_score,
                avg_novelty_ratio=summary.avg_novelty_ratio,
                plans_generated_last_30_days=summary.plans_generated_last_30_days,
                workouts_completed_last_7_days=summary.workouts_completed_last_7_days,
                plans_generated_this_week=summary.plans_generated_this_week,
                plans_generated_prev_week=summary.plans_generated_prev_week,
                workouts_completed_this_week=summary.workouts_completed_this_week,
                workouts_completed_prev_week=summary.workouts_completed_prev_week,
                retention_cohorts=[
                    WorkoutRetentionCohortOut(
                        cohort_week=item.cohort_week,
                        users_count=item.users_count,
                        d7_rate=item.d7_rate,
                        d30_rate=item.d30_rate,
                    )
                    for item in summary.retention_cohorts
                ],
                cycle_funnel=[
                    WorkoutCycleFunnelStepOut(
                        step_key=item.step_key,
                        title=item.title,
                        users_count=item.users_count,
                        conversion_from_prev=item.conversion_from_prev,
                    )
                    for item in summary.cycle_funnel
                ],
                alerts=[
                    WorkoutAnalyticsAlertOut(
                        code=item.code,
                        severity=item.severity,
                        title=item.title,
                        description=item.description,
                    )
                    for item in summary.alerts
                ],
            )
        )

