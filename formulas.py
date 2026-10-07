"""Боевые и экономические формулы баланса."""
from bot.config.constants import MORALE_BASE


def unit_cost(level: int, base_cost: int) -> int:
    """Стоимость постройки/апгрейда: растёт экспоненциально с уровнем."""
    return int(base_cost * (1.6 ** (level - 1)))


def production_amount(base: int, level: int) -> int:
    """Почасовой выход постройки: линейный рост + ускорение на высоких уровнях."""
    return int(base * level * (1 + 0.1 * (level - 1)))


def army_attack(units: dict[str, int], unit_stats: dict, morale: float = MORALE_BASE,
                terrain_bonus: float = 1.0) -> float:
    """Атака = Σ(кол-во × атака) × мораль × бонус местности."""
    return sum(units.get(t, 0) * unit_stats[t]["attack"] for t in units) * morale * terrain_bonus


def army_defense(units: dict[str, int], unit_stats: dict, wall_level: int = 0,
                 morale: float = MORALE_BASE) -> float:
    """Защита = Σ(кол-во × защита) × бонус стен × мораль. Стена: +8% за уровень."""
    base = sum(units.get(t, 0) * unit_stats[t]["defense"] for t in units)
    return base * (1 + 0.08 * wall_level) * morale


def losses(attacker_power: float, defender_power: float, hp: int) -> int:
    """Потери = min(урон / HP, кол-во войск) — пропорционально разнице сил."""
    if defender_power <= 0:
        return 1.0
    ratio = attacker_power / defender_power
    return min(ratio, 1.0) / hp * 100
