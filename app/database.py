"""
QRes OS 4 - Database Configuration
Настройка подключения к базе данных с поддержкой async SQLAlchemy 2.0
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, text
from datetime import datetime
from typing import AsyncGenerator

from .config import settings


# Создание асинхронного движка
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Логирование SQL-запросов в режиме отладки
    future=True,
    pool_pre_ping=True,  # Проверка соединений
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    
    # Автоматические поля времени для всех моделей с московским временем
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=text("datetime('now', '+3 hours')"),  # UTC + 3 часа для Москвы
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=text("datetime('now', '+3 hours')"),  # UTC + 3 часа для Москвы
        onupdate=text("datetime('now', '+3 hours')"),
        nullable=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД
    Используется в FastAPI Depends()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            # Логируем только реальные ошибки БД, не validation errors
            if "ValidationError" not in str(type(e)):
                from .logger import api_logger
                api_logger.error(f"Ошибка базы данных: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    # Импортируем все модели, чтобы SQLAlchemy знал о них
    from .models import (
        User, Location, Table, Category, Dish, DishVariation,
        Ingredient, PaymentMethod, Order, OrderItem
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие подключения к БД"""
    await engine.dispose()
