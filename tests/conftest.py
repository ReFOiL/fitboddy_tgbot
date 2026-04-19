"""Общие фикстуры для тестов."""
from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Добавляем корневую директорию проекта в sys.path для импортов
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.domain.entities.base import Base
from src.domain.entities import (  # noqa: F401 — побочный эффект: все ORM-модели в реестре до первого User()
    admin_account,
    contraindication,
    exercise,
    muscle,
    payment,
    questionnaire,
    training_plan,
    user,
    user_answer,
)
from src.domain.entities.equipment import Equipment
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption, CustomQuestionScoringWeight
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.user import User, Tariff
from src.domain.value_objects.questionnaire import AnswerType


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт изолированную БД в памяти для каждого теста."""
    try:
        from aiosqlite import __version__  # type: ignore[import-untyped]
    except ImportError:
        pytest.skip("aiosqlite not installed")
    
    # Используем SQLite в памяти для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest.fixture
async def sample_equipment(db_session: AsyncSession) -> list[Equipment]:
    """Создаёт тестовое оборудование."""
    equipment_list: list[Equipment] = [
        Equipment(
            name="dumbbells",
            display_name="Гантели",
            category="free_weights",
            is_home_friendly=True,
            is_active=True,
        ),
        Equipment(
            name="barbell",
            display_name="Штанга",
            category="free_weights",
            is_home_friendly=False,
            is_active=True,
        ),
        Equipment(
            name="none",
            display_name="Нет оборудования",
            category="bodyweight",
            is_home_friendly=True,
            is_active=True,
        ),
        Equipment(
            name="resistance_bands",
            display_name="Резинки",
            category="bodyweight",
            is_home_friendly=True,
            is_active=True,
        ),
    ]
    db_session.add_all(equipment_list)
    await db_session.flush()
    return equipment_list


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Создаёт тестового пользователя."""
    user: User = User(
        telegram_id=12345,
        username="test_user",
        tariff=Tariff.FREE,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def sample_custom_questions(db_session: AsyncSession) -> list[CustomQuestion]:
    """Создаёт тестовые кастомные вопросы."""
    questions: list[CustomQuestion] = [
        CustomQuestion(
            key="custom:preferred_time",
            order=1,
            text="Предпочитаемое время тренировок",
            answer_type=AnswerType.SINGLE_CHOICE,
            is_active=True,
            options=[
                CustomQuestionOption(value="morning", label="Утро", sort_order=1),
                CustomQuestionOption(value="evening", label="Вечер", sort_order=2),
            ],
        ),
        CustomQuestion(
            key="custom:stress_level",
            order=2,
            text="Уровень стресса",
            answer_type=AnswerType.NUMBER,
            is_active=True,
        ),
    ]
    db_session.add_all(questions)
    await db_session.flush()
    return questions


@pytest.fixture
async def sample_scoring_weights(
    db_session: AsyncSession, sample_custom_questions: list[CustomQuestion]
) -> list[CustomQuestionScoringWeight]:
    """Создаёт тестовые веса для вопросов."""
    weights: list[CustomQuestionScoringWeight] = [
        CustomQuestionScoringWeight(
            question_id=sample_custom_questions[0].id,
            answer_value="morning",
            weight=20,
        ),
        CustomQuestionScoringWeight(
            question_id=sample_custom_questions[0].id,
            answer_value="evening",
            weight=-10,
        ),
    ]
    db_session.add_all(weights)
    await db_session.flush()
    return weights
