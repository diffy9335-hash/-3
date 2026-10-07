"""Фоновые задачи APScheduler: почасовое производство, завершение строек,
регенерация. Вызываются из main.py."""
from loguru import logger

from bot.database import SessionLocal
from bot.services import economy_service


async def job_hourly_production() -> None:
    async with SessionLocal() as session:
        await economy_service.hourly_production(session)
    logger.info("hourly production tick done")


async def job_complete_constructions() -> None:
    async with SessionLocal() as session:
        done = await economy_service.complete_constructions(session)
    if done:
        logger.info(f"constructions completed: {done}")


async def job_regen() -> None:
    """Регенерация армии / проверка осад — заглушка для этапа 2+."""
    logger.debug("regen tick")
