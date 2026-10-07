"""Подключение к PostgreSQL и сессии. Для MVP — create_all;
в проде миграции переводим на Alembic (папка migrations/)."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from bot.config.settings import settings
from bot.models import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency-генератор сессий для хэндлеров и задач."""
    async with SessionLocal() as session:
        yield session
