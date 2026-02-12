from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from src.presentation.telegram_bot.handlers.start import router as start_router
from src.presentation.telegram_bot.handlers.questionnaire.flow import router as questionnaire_router
from src.presentation.telegram_bot.handlers.workouts.generate import router as workouts_router
from src.presentation.telegram_bot.handlers.workout import router as workout_router
from src.presentation.telegram_bot.middlewares.logging import LoggingMiddleware
from src.presentation.telegram_bot.middlewares.metrics import MetricsMiddleware


def create_dispatcher(storage: BaseStorage | None = None) -> Dispatcher:
    dp = Dispatcher(storage=storage)
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(MetricsMiddleware())
    dp.include_router(start_router)
    dp.include_router(questionnaire_router)
    dp.include_router(workouts_router)
    dp.include_router(workout_router)
    return dp

