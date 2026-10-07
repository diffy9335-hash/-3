"""Бизнес-логика экономики: строительство, производство, доходы с территорий."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.constants import BUILDINGS, BUILD_MAX_LEVEL, UNITS
from bot.config.settings import settings
from bot.models import ArmyUnit, Building, Nation, Region, Resources, User
from bot.services.cache import invalidate_army
from bot.utils.formulas import production_amount, unit_cost


def building_cost(building_type: str, level: int) -> tuple[int, str]:
    spec = BUILDINGS[building_type]
    return unit_cost(level + 1, spec["base_cost"]), spec["cost_type"]


async def get_or_create_resources(session: AsyncSession, user_id: int) -> Resources:
    res = await session.get(Resources, user_id)
    if res is None:
        res = Resources(user_id=user_id)
        session.add(res)
        await session.flush()
    return res


async def start_construction(session: AsyncSession, user_id: int, building_type: str) -> tuple[bool, str]:
    if building_type not in BUILDINGS:
        return False, "Неизвестное здание."

    res = await get_or_create_resources(session, user_id)
    existing = (await session.execute(
        select(Building).where(Building.user_id == user_id, Building.type == building_type)
    )).scalar_one_or_none()

    current_level = existing.level if existing else 0
    if current_level >= BUILD_MAX_LEVEL:
        return False, f"{BUILDINGS[building_type]['name']} уже максимального уровня ({BUILD_MAX_LEVEL})."
    if existing and existing.finishes_at and existing.finishes_at > datetime.now(timezone.utc):
        return False, "Это здание уже строится/улучшается."

    price, currency = building_cost(building_type, current_level)
    balance = getattr(res, currency)
    if balance < price:
        return False, f"Не хватает ресурсов: нужно {price} {currency}, у вас {balance}."

    setattr(res, currency, balance - price)
    hours = BUILDINGS[building_type]["hours"] + current_level
    if existing is None:
        session.add(Building(user_id=user_id, type=building_type, level=0,
                             finishes_at=datetime.now(timezone.utc) + timedelta(hours=hours)))
    else:
        existing.finishes_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    await session.commit()
    return True, f"{BUILDINGS[building_type]['emoji']} Строительство начато! Готово через {hours} ч."


async def complete_constructions(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    rows = (await session.execute(
        select(Building).where(Building.finishes_at.is_not(None), Building.finishes_at <= now)
    )).scalars().all()
    for b in rows:
        b.level += 1
        b.finishes_at = None
    await session.commit()
    return len(rows)


async def hourly_production(session: AsyncSession) -> None:
    """Почасовой тик: постройки + налоги с населения + доходы с территорий; армия ест еду."""
    now = datetime.now(timezone.utc)
    rows = (await session.execute(select(Building).where(Building.finishes_at.is_(None)))).scalars().all()
    cache: dict[int, float] = {}
    for b in rows:
        if b.level <= 0:
            continue
        res = await get_or_create_resources(session, b.user_id)
        if b.user_id not in cache:
            user = await session.get(User, b.user_id)
            nation = await session.get(Nation, user.nation_id) if user and user.nation_id else None
            cache[b.user_id] = 1 + (nation.bonus_economy / 100 if nation else 0)
        mult = cache[b.user_id]
        for resource, base in BUILDINGS[b.type]["produces"].items():
            amount = int(production_amount(base, b.level) * mult)
            setattr(res, resource, max(0, getattr(res, resource) + amount))

    # Налоги с населения и доходы с регионов (10% от value, ресурс региона — бонус)
    users = (await session.execute(select(User.telegram_id))).scalars().all()
    for uid in users:
        res = await get_or_create_resources(session, uid)
        tax = int(res.population * 0.01)  # 1% ВВП населения в час
        res.money += tax
    regions = (await session.execute(select(Region).where(Region.owner_id.is_not(None)))).scalars().all()
    for reg in regions:
        res = await get_or_create_resources(session, reg.owner_id)
        res.money += max(1, reg.value // 50)
        if reg.resource:
            setattr(res, reg.resource, getattr(res, reg.resource) + 5)

    # Содержание армии
    units = (await session.execute(select(ArmyUnit).where(ArmyUnit.count > 0))).scalars().all()
    for u in units:
        res = await get_or_create_resources(session, u.user_id)
        res.food = max(0, res.food - UNITS[u.unit_type]["upkeep"] * u.count)

    await session.commit()


async def daily_bonus(session: AsyncSession, user: User) -> tuple[bool, str]:
    now = datetime.now(timezone.utc)
    if user.last_daily and (now - user.last_daily).total_seconds() < 20 * 3600:
        return False, "Ежедневный бонус уже получен. Заходите позже!"
    res = await get_or_create_resources(session, user.telegram_id)
    res.money += settings.DAILY_BONUS_MONEY
    res.food += 100
    user.last_daily = now
    await session.commit()
    return True, f"🎁 Ежедневный бонус: +{settings.DAILY_BONUS_MONEY} 💵 и +100 🌾!"


async def spend_for_units(session: AsyncSession, user_id: int) -> None:
    """Хелпер: после найма/потерь армии инвалидируем кэш."""
    await invalidate_army(user_id)
