"""Карта мира: /map, /region, /claim — сетка 20×20."""
import random

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select

from bot.database import SessionLocal
from bot.models.region import MAP_SIZE, Region
from bot.models.user import User
from bot.config.constants import UNITS
from bot.services import battle_service

router = Router()

TERRAIN_EMOJI = {"plains": "🟩", "forest": "🌲", "mountain": "⛰️", "water": "🌊"}


async def seed_regions() -> None:
    """Заполнить мир 20×20 (только если пусто). Вызывается при старте."""
    async with SessionLocal() as session:
        count = (await session.execute(select(Region.id).limit(1))).first()
        if count:
            return
        random.seed(42)
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                rid = y * MAP_SIZE + x
                terrain = random.choices(["plains", "forest", "mountain", "water"],
                                         weights=[55, 25, 15, 5])[0]
                session.add(Region(
                    id=rid, x=x, y=y,
                    name=f"Регион {rid}",
                    terrain=terrain,
                    is_water=(terrain == "water"),
                    resource=random.choice([None, None, "iron", "oil", "food"]),
                    population=random.randint(200, 2000),
                    value=random.randint(50, 500),
                ))
        await session.commit()


def render_map(regions: list[Region], flags: dict[int, str]) -> str:
    """Сетка: нейтралы — рельеф, владения — флаг нации, столицы — ⭐."""
    grid = {}
    for r in regions:
        if r.is_water:
            grid[(r.x, r.y)] = "🌊"
        elif r.is_capital:
            grid[(r.x, r.y)] = "⭐"
        elif r.owner_id:
            grid[(r.x, r.y)] = flags.get(r.owner_id, "🚩")
        else:
            grid[(r.x, r.y)] = TERRAIN_EMOJI.get(r.terrain, "🟩")
    lines = []
    for y in range(MAP_SIZE):
        lines.append("".join(grid.get((x, y), "⬛") for x in range(MAP_SIZE)))
    return "\n".join(lines)


@router.message(Command("map"))
async def cmd_map(message: Message) -> None:
    async with SessionLocal() as session:
        regions = (await session.execute(select(Region))).scalars().all()
        owners = {r.owner_id for r in regions if r.owner_id}
        flags = {}
        for uid in owners:
            u = await session.get(User, uid)
            if u and u.nation_id:
                from bot.models import Nation
                n = await session.get(Nation, u.nation_id)
                flags[uid] = n.flag if n else "🚩"
    await message.answer(
        "🗺️ **Карта мира** (20×20)\n"
        "🟩 равнина 🌲 лес ⛰️ горы 🌊 вода ⭐ столица\n\n" + render_map(regions, flags),
        parse_mode="Markdown",
    )


@router.message(Command("region"))
async def cmd_region(message: Message, command: CommandObject) -> None:
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Использование: /region <id> (0–399)")
        return
    async with SessionLocal() as session:
        region = await session.get(Region, int(command.args.strip()))
        if not region:
            await message.answer("Регион не найден.")
            return
        owner = await session.get(User, region.owner_id) if region.owner_id else None
    await message.answer(
        f"📍 **{region.name}** (id: {region.id})\n"
        f"Координаты: {region.x},{region.y}\n"
        f"Рельеф: {region.terrain}\n"
        f"Ресурс: {region.resource or 'нет'}\n"
        f"Население: {region.population}\n"
        f"Ценность/оборона: {region.value}\n"
        f"Владелец: {owner.display_name() if owner else '— нейтрален —'}",
        parse_mode="Markdown",
    )


@router.message(Command("claim"))
async def cmd_claim(message: Message, command: CommandObject) -> None:
    """Захват нейтрального региона: армия должна превосходить оборону."""
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Использование: /claim <id региона>")
        return
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user or user.nation_id is None:
            await message.answer("Сначала /start")
            return
        region = await session.get(Region, int(command.args.strip()))
        if not region or region.is_water:
            await message.answer("❌ Нельзя захватить этот регион.")
            return
        if region.owner_id == user.telegram_id:
            await message.answer("Это уже ваш регион.")
            return
        if region.owner_id is not None:
            await message.answer("❌ Регион занят. Захват чужих территорий — через войну (/war <id>).")
            return
        army = await battle_service.get_army(session, user.telegram_id)
        power = sum(army.get(t, 0) * UNITS[t]["attack"] for t in army)
        if power < region.value:
            await message.answer(f"❌ Сила армии {int(power)} < обороны {region.value}. Наймите больше войск!")
            return
        region.owner_id = user.telegram_id
        await session.commit()
    await message.answer(f"🚩 {region.name} присоединён к вашему государству! (+💵/час, ресурс: {region.resource or 'нет'})")
