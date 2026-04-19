from __future__ import annotations

from aiogram import Router

from src.presentation.telegram_bot.handlers.workout.exercise_view import router as exercise_router
from src.presentation.telegram_bot.handlers.workout.my_plan import router as my_plan_router
from src.presentation.telegram_bot.handlers.workout.plan_callbacks import router as plan_callbacks_router
from src.presentation.telegram_bot.handlers.workout.progress import router as progress_router
from src.presentation.telegram_bot.handlers.workout.workout_day import router as today_router

router = Router(name="workout")
router.include_router(plan_callbacks_router)
router.include_router(my_plan_router)
router.include_router(today_router)
router.include_router(exercise_router)
router.include_router(progress_router)
