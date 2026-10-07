"""Тонкая обёртка над Redis: кэш армий, FSM-хранилище, локи."""
from redis.asyncio import Redis

from bot.config.settings import settings

_redis: Redis | None = None


def get_redis() -> Redis | None:
    """Ленивая инициализация клиента. Возвращает None, если Redis выключен."""
    global _redis
    if not settings.USE_REDIS:
        return None
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_cached_army(user_id: int) -> dict | None:
    r = get_redis()
    if r is None:
        return None
    import json
    raw = await r.get(f"army:{user_id}")
    return json.loads(raw) if raw else None


async def set_cached_army(user_id: int, army: dict, ttl: int = 300) -> None:
    r = get_redis()
    if r is not None:
        import json
        await r.set(f"army:{user_id}", json.dumps(army), ex=ttl)


async def invalidate_army(user_id: int) -> None:
    r = get_redis()
    if r is not None:
        await r.delete(f"army:{user_id}")
