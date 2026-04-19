"""Колбэки: выбор тренировки из плана, завершение, оценка нагрузки."""
from __future__ import annotations

import structlog
from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines, workout_title
from src.application.services.user_plan_service import UserPlanService
from src.domain.entities.training_plan import ScheduledWorkout
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


def _scaled_int(value: int | None, mult: float) -> int | None:
    if value is None:
        return None
    return max(1, int(round(value * mult)))


def _format_workout_detail(sw: ScheduledWorkout) -> tuple[str, InlineKeyboardMarkup]:
    title = workout_title(sw)
    mult = float(sw.volume_multiplier or 1.0)
    lines = [BotTexts.WORKOUT_DETAIL_HEADER, "", title, f"Объём недели: ×{mult:.1f}", ""]
    ordered = ordered_lines(sw)
    for i, we in enumerate(ordered, start=1):
        name = we.exercise.name if we.exercise else "—"
        sets = _scaled_int(we.sets, mult)
        reps = _scaled_int(we.reps, mult)
        part = ""
        if sets and reps:
            part = f"{sets}×{reps}"
        elif we.duration_seconds:
            dur = _scaled_int(we.duration_seconds, mult) or we.duration_seconds
            part = f"{dur} сек"
        lines.append(f"{i}. {name}" + (f" — {part}" if part else ""))

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"{i}. {we.exercise.name if we.exercise else '—'}",
                callback_data=f"exercise:{sw.id}:{i}",
            )
        ]
        for i, we in enumerate(ordered, start=1)
    ]
    if not sw.is_completed:
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"complete_workout:{sw.id}",
                )
            ]
        )
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


async def _scheduled_for_user(
    uow: UnitOfWork,
    user_id: int,
    scheduled_id: int,
) -> ScheduledWorkout | None:
    sw = await uow.scheduled_workouts.get_by_id(scheduled_id)
    if sw is None or sw.plan is None:
        return None
    if sw.plan.user_id != user_id:
        return None
    return sw


@router.callback_query(F.data.startswith("workout:"))
@inject
async def cb_workout_detail(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    try:
        sid = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    async with uow:
        user = await uow.users.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
            return
        sw = await _scheduled_for_user(uow, user.id, sid)
        if not sw or not ordered_lines(sw):
            await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
            return
        text, markup = _format_workout_detail(sw)

    await callback.answer()
    logger.info("bot.workout.plan_detail", user_id=user.id, scheduled_id=sid)
    await callback.message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("complete_workout:"))
@inject
async def cb_complete_workout(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    try:
        sid = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    async with uow:
        user = await uow.users.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
            return
        sw = await _scheduled_for_user(uow, user.id, sid)
        if not sw:
            await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
            return
        if sw.is_completed:
            await callback.answer(BotTexts.DONE_ALREADY, show_alert=True)
            return
        await uow.scheduled_workouts.mark_completed(sid)
        await uow.commit()
        logger.info("bot.workout.completed_callback", user_id=user.id, scheduled_id=sid)

    effort_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Легко", callback_data=f"effort:easy:{sid}"),
                InlineKeyboardButton(text="Нормально", callback_data=f"effort:ok:{sid}"),
                InlineKeyboardButton(text="Тяжело", callback_data=f"effort:hard:{sid}"),
            ]
        ]
    )
    await callback.answer()
    await callback.message.answer(BotTexts.DONE_OK + "\n\n" + BotTexts.EFFORT_PROMPT, reply_markup=effort_kb)


@router.callback_query(F.data.startswith("effort:"))
@inject
async def cb_effort(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, level, sid_s = parts
    if level not in ("easy", "ok", "hard"):
        await callback.answer()
        return
    try:
        sid = int(sid_s)
    except ValueError:
        await callback.answer()
        return

    async with uow:
        user = await uow.users.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
            return
        sw = await _scheduled_for_user(uow, user.id, sid)
        if not sw:
            await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
            return
        await uow.scheduled_workouts.set_perceived_effort(sid, level)
        await uow.commit()
        logger.info("bot.workout.effort", user_id=user.id, scheduled_id=sid, level=level)

    await callback.answer()
    await callback.message.answer(BotTexts.EFFORT_SAVED, reply_markup=main_menu())
