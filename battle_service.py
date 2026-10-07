"""Боевой движок: NPC и PvP, кэш армий в Redis."""
from datetime import datetime, timezone
from random import uniform

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.constants import NPC_TARGETS, UNITS
from bot.models import ArmyUnit, Battle, Resources, User
from bot.services.cache import get_cached_army, invalidate_army, set_cached_army
from bot.services.economy_service import get_or_create_resources
from bot.utils.formulas import army_attack, army_defense, losses


async def get_army(session: AsyncSession, user_id: int) -> dict[str, int]:
    """Армия из Redis (TTL 5 мин) или из БД с прогревом кэша."""
    cached = await get_cached_army(user_id)
    if cached is not None:
        return cached
    rows = (await session.execute(select(ArmyUnit).where(ArmyUnit.user_id == user_id))).scalars().all()
    army = {r.unit_type: r.count for r in rows if r.count > 0}
    await set_cached_army(user_id, army)
    return army


async def _apply_losses(session: AsyncSession, user_id: int, unit_losses: dict[str, int]) -> None:
    for unit_type, lost in unit_losses.items():
        if lost <= 0:
            continue
        row = (await session.execute(select(ArmyUnit).where(
            ArmyUnit.user_id == user_id, ArmyUnit.unit_type == unit_type))).scalar_one_or_none()
        if row:
            row.count = max(0, row.count - lost)
    await invalidate_army(user_id)


def simulate_battle(attacker: dict[str, int], defender: dict[str, int], max_turns: int = 5,
                    defender_wall: int = 0) -> dict:
    """Пошаговый авто-бой двух армий. Возвращает лог, потери обеих сторон и исход."""
    att_power = army_attack(attacker, UNITS, morale=uniform(0.9, 1.1))
    def_power = army_defense(defender, UNITS, wall_level=defender_wall, morale=uniform(0.9, 1.1))
    log = [f"⚔️ Бой начался! Атака {int(att_power)} vs Защита {int(def_power)}"]

    if att_power <= 0 or def_power <= 0:
        winner = "attacker_win" if def_power <= 0 < att_power else "defender_win"
        log.append("🏆 Противник беззащитен!" if winner == "attacker_win" else "💀 Некого атаковать…")
        return {"status": winner, "att_losses": {}, "def_losses": defender if winner == "attacker_win" else {},
                "turns": 1, "log": log}

    total = att_power + def_power
    win_chance = att_power / total
    victory = uniform(0, 1) < win_chance
    turns = max(1, int(5 * (1 - win_chance) * uniform(0.7, 1.3)))

    att_loss_ratio = min(losses(def_power if victory else att_power, total, hp=100) * uniform(0.8, 1.2), 0.9)
    def_loss_ratio = min(losses(att_power if victory else def_power, total, hp=100) * uniform(0.8, 1.2), 0.9)

    att_losses = {t: int(c * att_loss_ratio) for t, c in attacker.items()}
    def_losses = {t: int(c * def_loss_ratio) for t, c in defender.items()}

    for turn in range(1, turns + 1):
        log.append(f"🔁 Раунд {turn}: урон атаки {int(att_power / turns)}, урон обороны {int(def_power / turns)}")
    status = "attacker_win" if victory else "defender_win"
    log.append("🏆 Атакующие победили!" if victory else "🛡️ Оборона устояла!")
    return {"status": status, "att_losses": att_losses, "def_losses": def_losses,
            "turns": turns, "log": log}


async def attack_npc(session: AsyncSession, user_id: int, target_key: str) -> Battle:
    target = NPC_TARGETS[target_key]
    army = await get_army(session, user_id)
    # NPC «армия» — абстрактная сила, маппим на пехоту для формулы
    defender = {"infantry": max(1, target["power"] // UNITS["infantry"]["defense"])}
    result = simulate_battle(army, defender)

    await _apply_losses(session, user_id, result["att_losses"])

    loot: dict[str, int] = {}
    if result["status"] == "attacker_win":
        res = await get_or_create_resources(session, user_id)
        for resource, amount in target["loot"].items():
            loot[resource] = amount
            setattr(res, resource, getattr(res, resource) + amount)

    battle = Battle(attacker_id=user_id, is_npc=True, npc_name=target["name"],
                    status=result["status"], turns=result["turns"],
                    log=result["log"] + ([f"🎁 Трофеи: {loot}"] if loot else []),
                    finished_at=datetime.now(timezone.utc))
    session.add(battle)
    await session.commit()
    return battle


async def attack_player(session: AsyncSession, attacker_id: int, defender_id: int) -> Battle | None:
    """PvP-атака. Защитник отбивается всей армией (без онлайна — авто-бой)."""
    if attacker_id == defender_id:
        return None
    attacker = await get_army(session, attacker_id)
    defender = await get_army(session, defender_id)
    if not attacker:
        return None

    from bot.models import Building
    wall = (await session.execute(select(func.max(Building.level)).where(
        Building.user_id == defender_id, Building.type == "wall"))).scalar() or 0

    result = simulate_battle(attacker, defender, defender_wall=wall)
    await _apply_losses(session, attacker_id, result["att_losses"])
    await _apply_losses(session, defender_id, result["def_losses"])

    loot: dict[str, int] = {}
    if result["status"] == "attacker_win":
        att_res = await get_or_create_resources(session, attacker_id)
        def_res = await session.get(Resources, defender_id)
        if def_res:
            for resource in ("money", "food", "iron"):
                amount = min(getattr(def_res, resource), int(getattr(def_res, resource) * 0.1))
                setattr(def_res, resource, getattr(def_res, resource) - amount)
                setattr(att_res, resource, getattr(att_res, resource) + amount)
                loot[resource] = amount

    battle = Battle(attacker_id=attacker_id, defender_id=defender_id, is_npc=False,
                    status=result["status"], turns=result["turns"],
                    log=result["log"] + ([f"🎁 Трофеи: {loot}"] if loot else []),
                    finished_at=datetime.now(timezone.utc))
    session.add(battle)
    await session.commit()
    return battle


async def recruit(session: AsyncSession, user_id: int, unit_type: str, count: int = 1) -> tuple[bool, str]:
    if unit_type not in UNITS or count <= 0:
        return False, "Неизвестный тип войск."
    res = await get_or_create_resources(session, user_id)
    spec = UNITS[unit_type]
    for resource, per in spec["cost"].items():
        need = per * count
        if getattr(res, resource) < need:
            return False, f"Не хватает {resource}: нужно {need}."
    for resource, per in spec["cost"].items():
        setattr(res, resource, getattr(res, resource) - per * count)

    row = (await session.execute(select(ArmyUnit).where(
        ArmyUnit.user_id == user_id, ArmyUnit.unit_type == unit_type))).scalar_one_or_none()
    if row:
        row.count += count
    else:
        session.add(ArmyUnit(user_id=user_id, unit_type=unit_type, count=count))
    await session.commit()
    await invalidate_army(user_id)
    return True, f"{spec['emoji']} Нанято {count} × {spec['name']}."


def defense_hint(defender: User, defender_army: dict) -> str:
    return f"🛡️ {defender.display_name()}: {sum(defender_army.values())} войск"
