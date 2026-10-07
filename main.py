"""Точка входа: бот, планировщик, Alembic-миграции, Redis, бэкапы."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from bot.config.constants import NATIONS
from bot.config.settings import settings
from bot.database import SessionLocal
from bot.handlers import get_handlers_router
from bot.handlers.map import seed_regions
from bot.middlewares.audit import AuditMiddleware
from bot.middlewares.ban import BanMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.models import Nation
from bot.tasks import backups, production


def make_storage():
    """FSM-хранилище: Redis в проде, Memory в dev (USE_REDES=false)."""
    if settings.USE_REDIS:
        from aiogram.fsm.storage.redis import RedisStorage
        logger.info("using RedisStorage")
        return RedisStorage.from_url(settings.REDIS_URL)
    logger.info("using MemoryStorage (dev)")
    return MemoryStorage()


async def run_migrations() -> None:
    """Alembic upgrade head. Первая миграция создаёт схему из метадаты моделей."""
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    logger.info("migrations applied")


async def seed_nations() -> None:
    async with SessionLocal() as session:
        for spec in NATIONS:
            code = spec["code"]
            from sqlalchemy import select
            exists = (await session.execute(select(Nation).where(Nation.code == code))).scalar_one_or_none()
            if exists is None:
                session.add(Nation(
                    name=spec["name"], code=spec["code"], flag=spec["flag"],
                    description=f"Великая держава {spec['name']}.",
                    bonus_economy=spec["bonus_economy"], bonus_army=spec["bonus_army"],
                    bonus_science=spec["bonus_science"], bonus_stability=spec["bonus_stability"]))
        await session.commit()
    logger.info("nations seeded")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(production.job_hourly_production, "interval",
                      minutes=settings.PRODUCTION_INTERVAL_MINUTES, id="production")
    scheduler.add_job(production.job_complete_constructions, "interval",
                      minutes=settings.TICK_INTERVAL_MINUTES, id="construction_tick")
    scheduler.add_job(production.job_regen, "interval",
                      minutes=settings.REGEN_INTERVAL_MINUTES, id="regen")
    scheduler.add_job(backups.job_backup_database, "cron", hour="*/6", id="backup",
                      replace_existing=True)
    return scheduler


async def main() -> None:
    logger.info("starting bot…")
    await run_migrations()
    await seed_nations()
    await seed_regions()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=make_storage())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    dp.message.middleware(AuditMiddleware())
    dp.callback_query.middleware(AuditMiddleware())
    dp.include_router(get_handlers_router())

    scheduler = build_scheduler()
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
