import asyncio
import signal

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from src.infrastructure.observability.opentelemetry_setup import setup_tracing
from src.infrastructure.observability.prometheus_metrics import setup_prometheus
import structlog

from src.infrastructure.observability.structlog_config import setup_structlog
from src.infrastructure.database.seed import (
    CustomQuestionSeeder,
    WorkoutMvpFixturesSeeder,
)
from src.presentation.telegram_bot.auto_import import import_handlers
from src.presentation.telegram_bot.dispatcher import create_dispatcher
from src.shared.config.settings import get_settings
from src.shared.di.bootstrap import build_container


async def _run_bot() -> None:
    settings = get_settings()
    setup_structlog()
    logger = structlog.get_logger()
    setup_tracing(settings.observability.service_name, settings.observability.otel_exporter_otlp_endpoint)
    setup_prometheus()

    import_handlers()

    container = build_container()

    bot: Bot = container.bot()
    redis = Redis.from_url(settings.redis.url)
    storage = RedisStorage(redis=redis)

    seeded_mvp = await WorkoutMvpFixturesSeeder(container.uow()).run()
    logger.info("seed.workout_mvp", added=seeded_mvp)
    seeded_questions = await CustomQuestionSeeder(container.uow()).run()
    logger.info("seed.custom_questions", added=seeded_questions)
    dp = create_dispatcher(storage=storage)

    stop_event = asyncio.Event()

    def _stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _stop)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            close_bot_session=True,
            stop_event=stop_event,
        )
    finally:
        await redis.close()


def main() -> None:
    asyncio.run(_run_bot())


if __name__ == "__main__":
    main()

