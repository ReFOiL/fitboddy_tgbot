"""Колбэки: выбор тренировки из плана, завершение, оценка нагрузки."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.metrics import workout_nudges_total
from src.application.use_cases.workout.callback import (
    CallbackUserNotFoundError,
    CallbackWorkoutAccessDeniedError,
    CallbackWorkoutAlreadyCompletedError,
    CallbackWorkoutNotFoundError,
    CompleteWorkoutRequest,
    CompleteWorkoutUseCase,
    GetWorkoutDetailUseCase,
    SaveEffortRequest,
    SaveReflectionRequest,
    SaveWorkoutEffortUseCase,
    SaveWorkoutReflectionUseCase,
    WorkoutDetailRequest,
)
from src.application.workout.feedback import WorkoutNudgePolicy
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.presenters.workout import (
    WorkoutCallbackPayloadParser,
    WorkoutDetailFormatter,
    WorkoutEffortKeyboardBuilder,
    WorkoutReflectionKeyboardBuilder,
)
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


@router.callback_query(F.data.startswith("workout:"))
@inject
async def cb_workout_detail(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    sid = WorkoutCallbackPayloadParser.int_after_prefix(callback.data, "workout:")
    if sid is None:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    try:
        detail = await GetWorkoutDetailUseCase(uow).get_detail(
            WorkoutDetailRequest(tg_user_id=callback.from_user.id, scheduled_id=sid)
        )
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except CallbackWorkoutNotFoundError:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    text, markup = WorkoutDetailFormatter().format_workout(detail.scheduled_workout)

    await callback.answer()
    logger.info("bot.workout.plan_detail", user_id=detail.user_id, scheduled_id=sid)
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
    sid = WorkoutCallbackPayloadParser.int_after_prefix(callback.data, "complete_workout:")
    if sid is None:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return

    try:
        user_id = await CompleteWorkoutUseCase(uow).complete(
            CompleteWorkoutRequest(tg_user_id=callback.from_user.id, scheduled_id=sid)
        )
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except CallbackWorkoutNotFoundError:
        await callback.answer(BotTexts.WORKOUT_NOT_FOUND, show_alert=True)
        return
    except CallbackWorkoutAlreadyCompletedError:
        await callback.answer(BotTexts.DONE_ALREADY, show_alert=True)
        return

    logger.info("bot.workout.completed_callback", user_id=user_id, scheduled_id=sid)

    effort_kb = WorkoutEffortKeyboardBuilder.build(sid)
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
    parsed = WorkoutCallbackPayloadParser.effort(callback.data)
    if parsed is None:
        await callback.answer()
        return
    level, sid = parsed

    try:
        user_id = await SaveWorkoutEffortUseCase(uow).save_effort(
            SaveEffortRequest(tg_user_id=callback.from_user.id, scheduled_id=sid, level=level)
        )
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except (CallbackWorkoutNotFoundError, CallbackWorkoutAccessDeniedError):
        await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
        return

    logger.info("bot.workout.effort", user_id=user_id, scheduled_id=sid, level=level)

    async with uow:
        recent_difficulties = await uow.workout_feedback.list_last_difficulties(user_id, limit=3)
    nudge = WorkoutNudgePolicy().build_nudge(recent_difficulties, level)
    workout_nudges_total.labels(kind=nudge.kind).inc()

    await callback.answer()
    await callback.message.answer(BotTexts.EFFORT_SAVED + "\n\n" + nudge.text)
    reflection_kb = WorkoutReflectionKeyboardBuilder.build(sid)
    await callback.message.answer(BotTexts.REFLECTION_PROMPT, reply_markup=reflection_kb)


@router.callback_query(F.data.startswith("reflect:"))
@inject
async def cb_reflection(
    callback: CallbackQuery,
    uow: UnitOfWork = Provide[Container.uow],
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    parsed = WorkoutCallbackPayloadParser.reflection(callback.data)
    if parsed is None:
        await callback.answer()
        return
    energy, sid = parsed
    try:
        user_id = await SaveWorkoutReflectionUseCase(uow).save_reflection(
            SaveReflectionRequest(
                tg_user_id=callback.from_user.id,
                scheduled_id=sid,
                energy=energy,
            )
        )
    except CallbackUserNotFoundError:
        await callback.answer(BotTexts.WORKOUTS_REGISTER_FIRST, show_alert=True)
        return
    except (CallbackWorkoutNotFoundError, CallbackWorkoutAccessDeniedError):
        await callback.answer(BotTexts.WORKOUT_NOT_YOURS, show_alert=True)
        return
    logger.info("bot.workout.reflection", user_id=user_id, scheduled_id=sid, energy=energy)
    await callback.answer()
    await callback.message.answer(BotTexts.REFLECTION_SAVED, reply_markup=main_menu())
