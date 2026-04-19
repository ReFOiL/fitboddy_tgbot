"""Создание первого суперпользователя админки из переменных окружения."""
from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.commons.passwords import hash_password
from src.domain.entities.admin_account import AdminAccount
from src.infrastructure.database.repositories.admin_account import AdminAccountRepository
from src.shared.config.settings import AppSettings

logger = structlog.get_logger()


async def ensure_bootstrap_admin_account(
    session_factory: async_sessionmaker[AsyncSession],
    settings: AppSettings,
) -> None:
    async with session_factory() as session:
        repo = AdminAccountRepository(session)
        if await repo.count() > 0:
            await session.commit()
            return
        pwd = settings.admin_bootstrap_password.strip()
        if not pwd:
            logger.error(
                "admin.bootstrap.missing_password",
                hint="Set ADMIN_BOOTSTRAP_PASSWORD when admin_accounts is empty",
            )
            await session.commit()
            return
        username = settings.admin_bootstrap_username.strip() or "admin"
        account = AdminAccount(
            username=username,
            password_hash=hash_password(pwd),
            is_superuser=True,
        )
        await repo.add(account)
        await session.commit()
        logger.info("admin.bootstrap.created", username=username)
