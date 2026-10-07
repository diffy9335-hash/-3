"""Конфигурация приложения. Все секреты — в .env (см. .env.example)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/strategy"
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False               # MVP: MemoryStorage, в проде — Redis
    ADMIN_IDS: list[int] = []
    PRODUCTION_INTERVAL_MINUTES: int = 60 # почасовой тик экономики
    REGEN_INTERVAL_MINUTES: int = 5       # регенерация/проверка осад
    TICK_INTERVAL_MINUTES: int = 1        # завершение строек, уведомления
    DAILY_BONUS_MONEY: int = 250


settings = Settings()
