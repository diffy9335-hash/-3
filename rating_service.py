"""Рейтинги и достижения: агрегаты по ресурсам, армии и территориям."""
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.constants import ACHIEVEMENTS, RESOURCE_WEIGHTS, UNITS
from bot.models import ArmyUnit, Battle, Building, Nation, Region, Resources, User


@dataclass
class PlayerStats:
    user_id: int
    name: str
    flag: str
    # ресурсы
    wealth: int = 0
    money: int = 0
    # армия
    units: int = 0
    power: int = 0
    # территории
    regions: int = 0
    land_value: int = 0
    land_pop: int = 0
    # бои / постройки (для достижений)
    wins: int = 0
    pvp_wins: int = 0
    defends: int = 0
    buildings: int = 0
    wall: int = 0


# board -> (заголовок, ключ сортировки, подпись значения)
BOARDS = {
    "res":  ("💰 Ресурсы",    lambda s: (s.wealth, s.money),       lambda s: f"{s.wealth:,} (💵 {s.money:,})"),
    "army": ("⚔️ Армия",      lambda s: (s.power, s.units),        lambda s: f"сила {s.power:,} · {s.units:,} ед."),
    "land": ("🗺️ Территории", lambda s: (s.regions, s.land_value), lambda s: f"{s.regions} рег. · нас. {s.land_pop:,}"),
}


def achievements_for(s: PlayerStats) -> list[dict]:
    """Список достижений с прогрессом: done / current / goal."""
    result = []
    for a in ACHIEVEMENTS:
        cur = getattr(s, a["stat"])
        result.append({**a, "current": cur, "done": cur >= a["goal"]})
    return result


def ach_count(s: PlayerStats) -> int:
    return sum(1 for a in achievements_for(s) if a["done"])


async def collect_stats(session: AsyncSession) -> dict[int, PlayerStats]:
    """Собирает статистику всех зарегистрированных, не забаненных игроков (несколько группировок)."""
    users = (await session.execute(
        select(User.telegram_id, User.nickname, User.username, Nation.flag)
        .select_from(User)
        .join(Nation, Nation.id == User.nation_id)
        .where(User.is_banned.is_(False))
    )).all()
    stats = {uid: PlayerStats(uid, nick or username or str(uid), flag)
             for uid, nick, username, flag in users}

    for res in (await session.execute(select(Resources))).scalars():
        s = stats.get(res.user_id)
        if s:
            s.money = res.money
            s.wealth = sum(getattr(res, k) * w for k, w in RESOURCE_WEIGHTS.items())

    rows = await session.execute(
        select(ArmyUnit.user_id, ArmyUnit.unit_type, ArmyUnit.count).where(ArmyUnit.count > 0))
    for uid, unit_type, count in rows:
        s, spec = stats.get(uid), UNITS.get(unit_type)
        if s and spec:
            s.units += count
            s.power += count * (spec["attack"] + spec["defense"])

    rows = await session.execute(
        select(Region.owner_id, func.count(Region.id),
               func.coalesce(func.sum(Region.value), 0), func.coalesce(func.sum(Region.population), 0))
        .where(Region.owner_id.is_not(None)).group_by(Region.owner_id))
    for uid, cnt, value, pop in rows:
        s = stats.get(uid)
        if s:
            s.regions, s.land_value, s.land_pop = cnt, int(value), int(pop)

    rows = await session.execute(
        select(Battle.attacker_id, Battle.is_npc, func.count(Battle.id))
        .where(Battle.status == "attacker_win", Battle.attacker_id.is_not(None))
        .group_by(Battle.attacker_id, Battle.is_npc))
    for uid, is_npc, cnt in rows:
        s = stats.get(uid)
        if s:
            s.wins += cnt
            if not is_npc:
                s.pvp_wins += cnt

    rows = await session.execute(
        select(Battle.defender_id, func.count(Battle.id))
        .where(Battle.status == "defender_win", Battle.defender_id.is_not(None))
        .group_by(Battle.defender_id))
    for uid, cnt in rows:
        s = stats.get(uid)
        if s:
            s.defends = cnt

    for uid, btype, level in await session.execute(select(Building.user_id, Building.type, Building.level)):
        s = stats.get(uid)
        if s and level >= 1:
            s.buildings += 1
            if btype == "wall":
                s.wall = max(s.wall, level)
    return stats


def build_board(stats: dict[int, PlayerStats], board: str, viewer_id: int, limit: int = 10):
    """Возвращает (топ-N, место зрителя | None, статистика зрителя | None)."""
    if board == "ach":
        key = lambda s: (ach_count(s), s.wins)
    else:
        key = BOARDS[board][1]
    ranked = sorted(stats.values(), key=lambda s: (key(s), -s.user_id), reverse=True)
    my_rank = next((i for i, s in enumerate(ranked, 1) if s.user_id == viewer_id), None)
    return ranked[:limit], my_rank, stats.get(viewer_id)
