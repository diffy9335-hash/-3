"""Бэкап PostgreSQL через pg_dump: раз в 6 часов, ротация 7 копий."""
import asyncio
import os
from datetime import datetime
from pathlib import Path

from loguru import logger

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
KEEP_LAST = 7


def _pg_dsn_parts() -> dict:
    """Разобрать DATABASE_URL postgresql+asyncpg://user:pass@host:5432/db."""
    from bot.config.settings import settings
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    from urllib.parse import urlparse
    p = urlparse(url)
    return {"user": p.username, "password": p.password, "host": p.hostname,
            "port": p.port or 5432, "db": p.path.lstrip("/")}


async def job_backup_database() -> None:
    dsn = _pg_dsn_parts()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone_utc()).strftime("%Y%m%d_%H%M%S")
    out = BACKUP_DIR / f"backup_{stamp}.dump"

    env = {**os.environ, "PGPASSWORD": dsn["password"] or ""}
    proc = await asyncio.create_subprocess_exec(
        "pg_dump", "-h", dsn["host"], "-p", str(dsn["port"]), "-U", dsn["user"],
        "-Fc", "-f", str(out), dsn["db"],
        env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode == 0:
        logger.info(f"backup created: {out.name}")
        # Ротация: оставляем последние KEEP_LAST
        dumps = sorted(BACKUP_DIR.glob("backup_*.dump"))
        for old in dumps[:-KEEP_LAST]:
            old.unlink(missing_ok=True)
            logger.info(f"rotated out: {old.name}")
    else:
        logger.error(f"pg_dump failed: {stderr.decode()}")


def timezone_utc():
    from datetime import timezone
    return timezone.utc
