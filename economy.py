"""Экономика: ресурсы, строительство, ежедневный бонус."""
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config.constants import BUILDINGS
from bot.database import SessionLocal
from bot.keyboards.main_menu import buildings_keyboard
from bot.models import Building, User
from bot.services import economy_service
from bot.utils.formatters import fmt_resources, progress_bar

router = Router()


async def _require_user(session, user_id: int) -> User | None:
    user = await session.get(User, user_id)
    return user if user and user.nation_id is not None else None


@router.message(Command("economy"))
async def cmd_economy(message: Message) -> None:
    async with SessionLocal() as session:
        user = await _require_user(session, message.from_user.id)
        if not user:
            await message.answer("Сначала /start")
            return
        res = await economy_service.get_or_create_resources(session, message.from_user.id)
        buildings = (await session.execute(
            __import__("sqlalchemy").select(Building).where(Building.user_id == user.telegram_id)
        )).scalars().all()

    lines = ["💰 **Экономика**\n" + fmt_resources(res) + "\n\n🏗️ Постройки:"]
    for b in sorted(buildings, key=lambda x: x.type):
        spec = BUILDINGS.get(b.type)
        if not spec:
            continue
        if b.finishes_at and b.finishes_at > datetime.now(timezone.utc):
            left = b.finishes_at - datetime.now(timezone.utc)
            lines.append(f"{spec['emoji']} {spec['name']} ур.{b.level} — ⏳ {left} осталось")
        else:
            lines.append(f"{spec['emoji']} {spec['name']} ур.{b.level}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("build"))
async def cmd_build(message: Message) -> None:
    await message.answer("🏗️ Выберите здание для строительства/апгрейда:",
                         reply_markup=buildings_keyboard())


@router.callback_query(F.data.startswith("build:"))
async def build_callback(callback: CallbackQuery) -> None:
    building_type = callback.data.split(":")[1]
    async with SessionLocal() as session:
        ok, text = await economy_service.start_construction(session, callback.from_user.id, building_type)
    await callback.answer(text, show_alert=not ok)


@router.message(Command("daily"))
async def cmd_daily(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("Сначала /start")
            return
        ok, text = await economy_service.daily_bonus(session, user)
    await message.answer(text)
