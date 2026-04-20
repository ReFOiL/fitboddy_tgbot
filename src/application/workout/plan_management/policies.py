from __future__ import annotations

from datetime import date

from src.domain.entities.training_plan import TrainingPlan, TrainingPlanStatus


class ActivePlanPolicy:
    def is_reusable(self, plan: TrainingPlan, today: date) -> bool:
        if today < plan.start_date:
            return True
        return self.is_active_for_date(plan, today) and not self.should_roll_forward(plan, today)

    @staticmethod
    def is_active_for_date(plan: TrainingPlan, on_date: date) -> bool:
        if plan.status != TrainingPlanStatus.ACTIVE:
            return False
        return plan.start_date <= on_date <= plan.end_date

    @staticmethod
    def should_roll_forward(plan: TrainingPlan, today: date) -> bool:
        if plan.status != TrainingPlanStatus.ACTIVE:
            return True
        if today > plan.end_date:
            return True
        return (today - plan.start_date).days >= 28
