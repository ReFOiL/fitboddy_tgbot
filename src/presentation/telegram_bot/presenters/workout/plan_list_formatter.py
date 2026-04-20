from __future__ import annotations

from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application.services.scheduled_workout_lines import workout_title
from src.application.use_cases.workout.query.models import MyPlanViewData
from src.presentation.telegram_bot.texts import BotTexts


class WorkoutPlanListFormatter:
    def format_plan(self, data: MyPlanViewData) -> tuple[str, InlineKeyboardMarkup | None]:
        plan = data.plan
        sorted_workouts = sorted(plan.scheduled_workouts, key=lambda item: item.scheduled_for)
        lines = [BotTexts.PLAN_HEADER, ""]
        if data.progress is not None:
            progress = data.progress
            lines.extend(
                [
                    f"Цикл #{progress.cycle_index} · этап: {self._phase_label(progress.phase)}",
                    (
                        f"Прогресс: {progress.completed_workouts}/{progress.planned_workouts} "
                        f"({int(progress.completion_rate * 100)}%)"
                    ),
                    "",
                ]
            )
        lines.extend(
            [
                "Статусы:",
                "🟢 Сегодня",
                "🔜 Впереди",
                "✅ Выполнено",
                "⏳ Пропущено",
                "",
            ]
        )
        rows: list[list[InlineKeyboardButton]] = []
        current_week: tuple[int, int] | None = None
        for workout in sorted_workouts:
            week_key = workout.scheduled_for.isocalendar()[:2]
            if week_key != current_week:
                current_week = week_key
                lines.extend(["", f"Неделя {workout.scheduled_for.isocalendar().week}"])
            title = workout_title(workout)
            status = self._status_icon(workout.scheduled_for, workout.is_completed)
            lines.append(f"{status} {workout.scheduled_for:%d.%m} — {title}")
            label = f"{workout.scheduled_for:%d.%m} {title}"[:60]
            rows.append([InlineKeyboardButton(text=label, callback_data=f"workout:{workout.id}")])
        focus_workout = self._focus_workout(sorted_workouts)
        if focus_workout is not None:
            focus_label = self._focus_button_label(focus_workout.scheduled_for, focus_workout.is_completed)
            rows.insert(
                0,
                [InlineKeyboardButton(text=focus_label, callback_data=f"workout:{focus_workout.id}")],
            )
        adaptive_hint = self._adaptive_plan_hint(data)
        if adaptive_hint:
            lines.extend(["", adaptive_hint])
        next_action = self._next_action_hint(data)
        if next_action:
            lines.extend(["", next_action])
        markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
        return "\n".join(lines), markup

    @staticmethod
    def _status_icon(scheduled_for: date, is_completed: bool) -> str:
        if is_completed:
            return "✅"
        if scheduled_for == date.today():
            return "🟢"
        if scheduled_for < date.today():
            return "⏳"
        return "🔜"

    @staticmethod
    def _phase_label(phase: str) -> str:
        labels = {
            "accumulation": "Набор объема",
            "intensification": "Усиление нагрузки",
            "deload": "Разгрузка",
            "recovery": "Восстановление",
        }
        return labels.get((phase or "").strip().lower(), "Рабочий этап")

    def _adaptive_plan_hint(self, data: MyPlanViewData) -> str | None:
        workouts = list(data.plan.scheduled_workouts)
        total = len(workouts)
        if total == 0:
            return None
        phase = (data.progress.phase if data.progress is not None else "").strip().lower()
        tone_suffix = self._feedback_tone_suffix(data)
        completed = sum(1 for workout in workouts if workout.is_completed)
        overdue = sum(
            1
            for workout in workouts
            if (not workout.is_completed) and workout.scheduled_for < date.today()
        )
        upcoming = sum(
            1
            for workout in workouts
            if (not workout.is_completed) and workout.scheduled_for >= date.today()
        )
        completion_rate = completed / total

        if completed == total:
            return (
                "🔥 План закрыт на 100%. Отличная дисциплина."
                f" {self._phase_guidance_done(phase)} {tone_suffix}"
            )
        if completion_rate >= 0.75:
            return (
                f"🚀 Сильный темп: {int(completion_rate * 100)}% уже выполнено. "
                f"Осталось дожать {upcoming} тренировк(и). "
                f"{self._phase_guidance_active(phase)} {tone_suffix}"
            )
        if completion_rate >= 0.35:
            if overdue > 0:
                return (
                    f"💪 Уже есть хороший прогресс: {completed}/{total}. "
                    f"Есть {overdue} пропущенных — можно вернуться в ритм с ближайшей сессии. "
                    f"{self._phase_guidance_recovery(phase)} {tone_suffix}"
                )
            return (
                f"💪 Вы в рабочем темпе: {completed}/{total}. "
                f"Продолжаем стабильно, без резких скачков. {self._phase_guidance_active(phase)} {tone_suffix}"
            )
        if completed > 0:
            return (
                f"🌱 Старт положен: {completed}/{total}. "
                f"Дальше важна регулярность — по одной тренировке за раз. {self._phase_guidance_start(phase)} {tone_suffix}"
            )
        if overdue > 0:
            return (
                f"🧭 План уже готов. Есть {overdue} пропущенных — "
                f"лучше вернуться с самой ближайшей тренировки. {self._phase_guidance_recovery(phase)} {tone_suffix}"
            )
        return (
            "🧭 План готов. Начните с тренировки на сегодня — дальше втянетесь в ритм. "
            f"{self._phase_guidance_start(phase)} {tone_suffix}"
        )

    @staticmethod
    def _phase_guidance_start(phase: str) -> str:
        if phase == "accumulation":
            return "Сейчас главное — собрать базовый объем."
        if phase == "intensification":
            return "Фокус этапа — качественная работа в основных упражнениях."
        if phase in {"deload", "recovery"}:
            return "Этот этап про мягкий вход и контроль самочувствия."
        return "Двигайтесь в комфортном, но стабильном ритме."

    @staticmethod
    def _phase_guidance_active(phase: str) -> str:
        if phase == "accumulation":
            return "Набираем объем без перегруза."
        if phase == "intensification":
            return "Держим качество техники и рабочую интенсивность."
        if phase in {"deload", "recovery"}:
            return "Не форсируйте темп: приоритет — восстановление."
        return "Сохраняйте ровный темп."

    @staticmethod
    def _phase_guidance_recovery(phase: str) -> str:
        if phase in {"deload", "recovery"}:
            return "Пропуски лучше закрывать мягко, без попытки догнать всё сразу."
        return "Вернитесь в план с ближайшей тренировки и держите темп."

    @staticmethod
    def _phase_guidance_done(phase: str) -> str:
        if phase == "accumulation":
            return "Базу объема собрали — можно аккуратно повышать сложность."
        if phase == "intensification":
            return "Сильный этап: можно планировать следующий шаг прогрессии."
        if phase in {"deload", "recovery"}:
            return "Восстановительный этап пройден отлично — организм скажет спасибо."
        return "Хороший результат, так держать."

    @staticmethod
    def _feedback_tone_suffix(data: MyPlanViewData) -> str:
        recent_difficulties = [item.strip().lower() for item in (data.recent_difficulties or []) if item]
        recent_energies = [str(item).strip().lower() for item in (data.recent_energies or []) if item]
        if not recent_difficulties and not recent_energies:
            return "📝 Подсказывайте ощущения после тренировок — так я точнее подстрою план."

        hard_n = sum(1 for item in recent_difficulties if item == "hard")
        easy_n = sum(1 for item in recent_difficulties if item == "easy")
        low_energy_n = sum(1 for item in recent_energies if item == "low")
        high_energy_n = sum(1 for item in recent_energies if item == "high")

        if hard_n >= 2 or low_energy_n >= 2:
            return "🤍 По последним ощущениям держим щадящий темп и ставим фокус на восстановление."
        if easy_n >= 2 and high_energy_n >= 2:
            return "⚡ По вашему самочувствию можно аккуратно добавлять сложность."
        if hard_n > easy_n or low_energy_n > high_energy_n:
            return "🌿 Если нагрузка тяжеловата, держим ровный ритм без форсирования."
        if easy_n > hard_n or high_energy_n > low_energy_n:
            return "🔥 Самочувствие стабильное — можно прогрессировать плавно."
        return "🙂 Держим устойчивый ритм и продолжаем отслеживать ощущения."

    @staticmethod
    def _next_action_hint(data: MyPlanViewData) -> str | None:
        workouts = sorted(data.plan.scheduled_workouts, key=lambda item: item.scheduled_for)
        if not workouts:
            return None
        today = date.today()
        overdue = [item for item in workouts if (not item.is_completed) and item.scheduled_for < today]
        today_items = [item for item in workouts if (not item.is_completed) and item.scheduled_for == today]
        upcoming = [item for item in workouts if (not item.is_completed) and item.scheduled_for > today]

        if today_items:
            workout = today_items[0]
            return f"👉 Следующий шаг: откройте «🏋️ На сегодня» и выполните тренировку {workout.scheduled_for:%d.%m}."
        if overdue:
            workout = overdue[0]
            return (
                f"👉 Следующий шаг: закройте ближайший пропуск от {workout.scheduled_for:%d.%m}, "
                "чтобы вернуть ритм."
            )
        if upcoming:
            workout = upcoming[0]
            return f"👉 Следующий шаг: подготовьтесь к тренировке {workout.scheduled_for:%d.%m}."
        return "✅ Все тренировки в плане уже закрыты. Можно восстановиться и ждать следующий цикл."

    @staticmethod
    def _focus_workout(workouts: list) -> object | None:
        if not workouts:
            return None
        today = date.today()
        for workout in workouts:
            if (not workout.is_completed) and workout.scheduled_for == today:
                return workout
        for workout in workouts:
            if (not workout.is_completed) and workout.scheduled_for < today:
                return workout
        for workout in workouts:
            if (not workout.is_completed) and workout.scheduled_for > today:
                return workout
        return workouts[-1]

    @staticmethod
    def _focus_button_label(scheduled_for: date, is_completed: bool) -> str:
        if is_completed:
            return "✅ Открыть последнюю выполненную"
        if scheduled_for == date.today():
            return "🟢 Перейти к тренировке на сегодня"
        if scheduled_for < date.today():
            return f"⏳ Закрыть пропуск {scheduled_for:%d.%m}"
        return f"🔜 Перейти к ближайшей {scheduled_for:%d.%m}"
