from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.training_plan import ScheduledWorkout
from src.domain.entities.user_answer import UserAnswer
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.shared.utils.profile_answers import AnswerLookup


@dataclass(slots=True)
class WorkoutAnalyticsSummary:
    users_total: int
    users_with_profile: int
    users_with_2_cycles: int
    d7_retention_rate: float
    d30_retention_rate: float
    avg_cycle_completion_rate: float
    avg_adherence_score: float
    avg_novelty_ratio: float
    plans_generated_last_30_days: int
    workouts_completed_last_7_days: int
    retention_cohorts: list["WorkoutRetentionCohort"]
    cycle_funnel: list["WorkoutCycleFunnelStep"]
    plans_generated_this_week: int
    plans_generated_prev_week: int
    workouts_completed_this_week: int
    workouts_completed_prev_week: int
    alerts: list["WorkoutAnalyticsAlert"]


@dataclass(slots=True)
class WorkoutRetentionCohort:
    cohort_week: str
    users_count: int
    d7_rate: float
    d30_rate: float


@dataclass(slots=True)
class WorkoutCycleFunnelStep:
    step_key: str
    title: str
    users_count: int
    conversion_from_prev: float


@dataclass(slots=True)
class WorkoutAnalyticsAlert:
    code: str
    severity: str
    title: str
    description: str


@dataclass(slots=True)
class WorkoutAnalyticsFilters:
    goal: str | None = None
    level: str | None = None
    workout_location: str | None = None
    equipment: str | None = None


class WorkoutAnalyticsAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_summary(
        self,
        filters: WorkoutAnalyticsFilters | None = None,
    ) -> WorkoutAnalyticsSummary:
        now = datetime.now(timezone.utc)
        recent_30 = now - timedelta(days=30)
        recent_7 = now - timedelta(days=7)
        this_week_start = now - timedelta(days=7)
        prev_week_start = now - timedelta(days=14)
        normalized_filters = filters or WorkoutAnalyticsFilters()

        async with self._uow:
            users = await self._uow.users.list_all()
            eligible_user_ids: list[int] = []
            for user in users:
                answers = await self._uow.user_answers.list_by_user_id(user.id)
                if self._matches_filters(answers, normalized_filters):
                    eligible_user_ids.append(user.id)
            users = [user for user in users if user.id in set(eligible_user_ids)]
            users_total = len(users)
            users_with_profile = sum(1 for user in users if user.has_completed_profile)

            d7_hits = 0
            d30_hits = 0
            plans_generated_last_30_days = 0
            workouts_completed_last_7_days = 0
            users_with_2_cycles = 0
            completion_scores: list[float] = []
            novelty_scores: list[float] = []
            cohort_map: dict[str, list[tuple[datetime, list[datetime]]]] = {}
            plans_generated_this_week = 0
            plans_generated_prev_week = 0
            workouts_completed_this_week = 0
            workouts_completed_prev_week = 0
            funnel_users_total = users_total
            funnel_plan_generated = 0
            funnel_started_first_cycle = 0
            funnel_completed_first_cycle = 0
            funnel_generated_second_cycle = 0
            funnel_started_second_cycle = 0

            for user in users:
                plans = await self._uow.training_plans.list_for_user(user.id, limit=30)
                created_at_utc = self._to_utc(user.created_at)
                completed_datetimes: list[datetime] = []
                if len(plans) >= 2:
                    users_with_2_cycles += 1
                plans_generated_last_30_days += sum(
                    1 for plan in plans if self._to_utc(plan.created_at) >= recent_30
                )
                plans_generated_this_week += sum(
                    1 for plan in plans if self._to_utc(plan.created_at) >= this_week_start
                )
                plans_generated_prev_week += sum(
                    1
                    for plan in plans
                    if prev_week_start <= self._to_utc(plan.created_at) < this_week_start
                )
                if plans:
                    funnel_plan_generated += 1
                if not plans:
                    cohort_key = f"{created_at_utc.isocalendar().year}-W{created_at_utc.isocalendar().week:02d}"
                    cohort_map.setdefault(cohort_key, []).append((created_at_utc, completed_datetimes))
                    continue

                user_workouts: list[ScheduledWorkout] = []
                for plan in plans:
                    user_workouts.extend(await self._uow.scheduled_workouts.list_by_plan_id(plan.id))
                completed_datetimes = [
                    self._to_utc(item.completed_at)
                    for item in user_workouts
                    if item.is_completed and item.completed_at is not None
                ]
                if completed_datetimes:
                    d7_deadline = self._to_utc(user.created_at) + timedelta(days=7)
                    d30_deadline = self._to_utc(user.created_at) + timedelta(days=30)
                    if any(ts <= d7_deadline for ts in completed_datetimes):
                        d7_hits += 1
                    if any(ts <= d30_deadline for ts in completed_datetimes):
                        d30_hits += 1
                    workouts_completed_last_7_days += sum(1 for ts in completed_datetimes if ts >= recent_7)
                    workouts_completed_this_week += sum(1 for ts in completed_datetimes if ts >= this_week_start)
                    workouts_completed_prev_week += sum(
                        1 for ts in completed_datetimes if prev_week_start <= ts < this_week_start
                    )
                cohort_key = f"{created_at_utc.isocalendar().year}-W{created_at_utc.isocalendar().week:02d}"
                cohort_map.setdefault(cohort_key, []).append((created_at_utc, completed_datetimes))

                first_cycle_workouts = await self._uow.scheduled_workouts.list_by_plan_id(plans[0].id)
                if any(item.is_completed for item in first_cycle_workouts):
                    funnel_started_first_cycle += 1
                if first_cycle_workouts and all(item.is_completed for item in first_cycle_workouts):
                    funnel_completed_first_cycle += 1
                if len(plans) >= 2:
                    funnel_generated_second_cycle += 1
                    second_cycle_workouts = await self._uow.scheduled_workouts.list_by_plan_id(plans[1].id)
                    if any(item.is_completed for item in second_cycle_workouts):
                        funnel_started_second_cycle += 1

                current_cycle = plans[0]
                current_workouts = await self._uow.scheduled_workouts.list_by_plan_id(current_cycle.id)
                completion = self._completion_rate(current_workouts)
                completion_scores.append(completion)

                previous_cycle = plans[1] if len(plans) > 1 else None
                if previous_cycle is not None:
                    previous_workouts = await self._uow.scheduled_workouts.list_by_plan_id(previous_cycle.id)
                    novelty_scores.append(self._novelty_ratio(current_workouts, previous_workouts))

            retention_cohorts = self._build_retention_cohorts(cohort_map)
            cycle_funnel = self._build_cycle_funnel(
                users_total=funnel_users_total,
                plan_generated=funnel_plan_generated,
                started_first_cycle=funnel_started_first_cycle,
                completed_first_cycle=funnel_completed_first_cycle,
                generated_second_cycle=funnel_generated_second_cycle,
                started_second_cycle=funnel_started_second_cycle,
            )
            alerts = self._build_alerts(
                avg_novelty=self._safe_avg(novelty_scores),
                avg_completion=self._safe_avg(completion_scores),
                d30_rate=self._safe_rate(d30_hits, users_total),
            )
            return WorkoutAnalyticsSummary(
                users_total=users_total,
                users_with_profile=users_with_profile,
                users_with_2_cycles=users_with_2_cycles,
                d7_retention_rate=self._safe_rate(d7_hits, users_total),
                d30_retention_rate=self._safe_rate(d30_hits, users_total),
                avg_cycle_completion_rate=self._safe_avg(completion_scores),
                avg_adherence_score=self._safe_avg(completion_scores),
                avg_novelty_ratio=self._safe_avg(novelty_scores),
                plans_generated_last_30_days=plans_generated_last_30_days,
                workouts_completed_last_7_days=workouts_completed_last_7_days,
                retention_cohorts=retention_cohorts,
                cycle_funnel=cycle_funnel,
                plans_generated_this_week=plans_generated_this_week,
                plans_generated_prev_week=plans_generated_prev_week,
                workouts_completed_this_week=workouts_completed_this_week,
                workouts_completed_prev_week=workouts_completed_prev_week,
                alerts=alerts,
            )

    @staticmethod
    def _to_utc(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    @staticmethod
    def _completion_rate(workouts: list[ScheduledWorkout]) -> float:
        if not workouts:
            return 0.0
        completed = sum(1 for item in workouts if item.is_completed)
        return round(completed / len(workouts), 3)

    @staticmethod
    def _novelty_ratio(current: list[ScheduledWorkout], previous: list[ScheduledWorkout]) -> float:
        current_ids = {
            line.exercise_id for workout in current for line in workout.session_exercises
        }
        if not current_ids:
            return 0.0
        prev_ids = {
            line.exercise_id for workout in previous for line in workout.session_exercises
        }
        fresh = current_ids - prev_ids
        return round(len(fresh) / len(current_ids), 3)

    @staticmethod
    def _safe_rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator, 3)

    @staticmethod
    def _safe_avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)

    def _build_retention_cohorts(
        self,
        cohort_map: dict[str, list[tuple[datetime, list[datetime]]]],
    ) -> list[WorkoutRetentionCohort]:
        rows: list[WorkoutRetentionCohort] = []
        for cohort_week in sorted(cohort_map.keys(), reverse=True)[:8]:
            bucket = cohort_map[cohort_week]
            users_count = len(bucket)
            if users_count <= 0:
                continue
            d7_hits = 0
            d30_hits = 0
            for created_at, completed_ts in bucket:
                d7_deadline = created_at + timedelta(days=7)
                d30_deadline = created_at + timedelta(days=30)
                if any(ts <= d7_deadline for ts in completed_ts):
                    d7_hits += 1
                if any(ts <= d30_deadline for ts in completed_ts):
                    d30_hits += 1
            rows.append(
                WorkoutRetentionCohort(
                    cohort_week=cohort_week,
                    users_count=users_count,
                    d7_rate=self._safe_rate(d7_hits, users_count),
                    d30_rate=self._safe_rate(d30_hits, users_count),
                )
            )
        return rows

    def _build_cycle_funnel(
        self,
        *,
        users_total: int,
        plan_generated: int,
        started_first_cycle: int,
        completed_first_cycle: int,
        generated_second_cycle: int,
        started_second_cycle: int,
    ) -> list[WorkoutCycleFunnelStep]:
        raw_steps = [
            ("users_total", "Пользователи", users_total),
            ("plan_generated", "Есть план", plan_generated),
            ("started_first_cycle", "Старт 1-го цикла", started_first_cycle),
            ("completed_first_cycle", "Финиш 1-го цикла", completed_first_cycle),
            ("generated_second_cycle", "Сгенерирован 2-й цикл", generated_second_cycle),
            ("started_second_cycle", "Старт 2-го цикла", started_second_cycle),
        ]
        out: list[WorkoutCycleFunnelStep] = []
        prev = None
        for step_key, title, users_count in raw_steps:
            conversion = 0.0 if not prev or prev <= 0 else self._safe_rate(users_count, prev)
            out.append(
                WorkoutCycleFunnelStep(
                    step_key=step_key,
                    title=title,
                    users_count=users_count,
                    conversion_from_prev=conversion,
                )
            )
            prev = users_count
        return out

    @staticmethod
    def _matches_filters(answers: list[UserAnswer], filters: WorkoutAnalyticsFilters) -> bool:
        lookup = AnswerLookup(answers)
        if filters.goal:
            if (lookup.get_str(SystemQuestionKey.GOAL) or "").strip().lower() != filters.goal:
                return False
        if filters.level:
            if (lookup.get_str(SystemQuestionKey.LEVEL) or "").strip().lower() != filters.level:
                return False
        if filters.workout_location:
            if (lookup.get_str(SystemQuestionKey.WORKOUT_LOCATION) or "").strip().lower() != filters.workout_location:
                return False
        if filters.equipment:
            values = [value.strip().lower() for value in lookup.get_values(SystemQuestionKey.EQUIPMENT)]
            if filters.equipment not in values:
                return False
        return True

    def _build_alerts(
        self,
        *,
        avg_novelty: float,
        avg_completion: float,
        d30_rate: float,
    ) -> list[WorkoutAnalyticsAlert]:
        alerts: list[WorkoutAnalyticsAlert] = []
        if avg_novelty < 0.35:
            alerts.append(
                WorkoutAnalyticsAlert(
                    code="low_novelty",
                    severity="warning",
                    title="Низкая новизна цикла",
                    description="Средний novelty ratio ниже 35%. Пользователи могут ощущать однообразие.",
                )
            )
        if avg_completion < 0.55:
            alerts.append(
                WorkoutAnalyticsAlert(
                    code="low_completion",
                    severity="critical",
                    title="Просадка completion rate",
                    description="Средняя завершенность цикла ниже 55%. Стоит снизить нагрузку и усилить nudges.",
                )
            )
        if d30_rate < 0.25:
            alerts.append(
                WorkoutAnalyticsAlert(
                    code="low_d30",
                    severity="critical",
                    title="Низкий D30 retention",
                    description="D30 ниже 25%. Проверь вовлечение после первой недели и качество второго цикла.",
                )
            )
        return alerts

