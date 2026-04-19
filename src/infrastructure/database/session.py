from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.config.settings import get_settings


def create_engine(database_url: str | None = None):
    """Если ``database_url`` не передан (вне DI), читаем URL из ``get_settings()``."""
    url = database_url if database_url is not None else get_settings().database.url
    return create_async_engine(url, future=True, echo=False)


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

