"""Отметка «выполнено» для тренировки на сегодня (кнопка меню)."""
from __future__ import annotations

import structlog

from aiogram import F, Router
from aiogram.types import Message
from dependency_injector.wiring import Provide, inject

from src.application.use_cases.workout.query import (
    CompleteTodayWorkoutUseCase,
    WorkoutQueryAlreadyCompleted,
    WorkoutQueryPlanNotFound,
    WorkoutQueryTodayWorkoutNotFound,
    WorkoutQueryUserNotFound,
)
from src.presentation.telegram_bot.keyboards.builders import main_menu, MENU_MARK_DONE
from src.presentation.telegram_bot.presenters.workout import WorkoutEffortKeyboardBuilder
from src.presentation.telegram_bot.texts import BotTexts
from src.shared.di import Container

logger = structlog.get_logger()

router = Router()


@router.message(F.text == MENU_MARK_DONE)
@inject
async def cmd_done(
    message: Message,
    use_case: CompleteTodayWorkoutUseCase = Provide[Container.complete_today_workout_use_case],
) -> None:
    if not message.from_user:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
        return

    try:
        completed = await use_case.complete_today(message.from_user.id)
    except WorkoutQueryUserNotFound:
        await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
        return
    except WorkoutQueryPlanNotFound:
        await message.answer(BotTexts.PLAN_NO_PLAN, reply_markup=main_menu())
        return
    except WorkoutQueryTodayWorkoutNotFound:
        await message.answer(BotTexts.TODAY_NO_WORKOUT, reply_markup=main_menu())
        return
    except WorkoutQueryAlreadyCompleted:
        await message.answer(BotTexts.DONE_ALREADY, reply_markup=main_menu())
        return

    logger.info(
        "bot.workout.completed",
        user_id=completed.user_id,
        telegram_id=completed.telegram_id,
        scheduled_workout_id=completed.scheduled_workout_id,
        scheduled_for=completed.scheduled_for_iso,
    )
    effort_kb = WorkoutEffortKeyboardBuilder.build(completed.scheduled_workout_id)
    await message.answer(BotTexts.DONE_OK + "\n\n" + BotTexts.EFFORT_PROMPT, reply_markup=effort_kb)
