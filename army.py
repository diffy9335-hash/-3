"""Армия: просмотр войск, найм."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config.constants import UNITS
from bot.database import SessionLocal
from bot.keyboards.main_menu import army_keyboard
from bot.models import User
from bot.services import battle_service

router = Router()


@router.message(Command("army"))
async def cmd_army(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user or user.nation_id is None:
            await message.answer("Сначала /start")
            return
        army = await battle_service.get_army(session, message.from_user.id)

    lines = ["⚔️ **Ваша армия**"]
    total_upkeep = 0
    for key, spec in UNITS.items():
        count = army.get(key, 0)
        total_upkeep += spec["upkeep"] * count
        lines.append(f"{spec['emoji']} {spec['name']}: {count} (А{spec['attack']}/З{spec['defense']})")
    lines.append(f"\n💸 Содержание: {total_upkeep} 🌾/час")
    await message.answer("\n".join(lines), parse_mode="Markdown", reply_markup=army_keyboard())


@router.callback_query(F.data.startswith("recruit:"))
async def recruit_callback(callback: CallbackQuery) -> None:
    unit_type = callback.data.split(":")[1]
    async with SessionLocal() as session:
        ok, text = await battle_service.recruit(session, callback.from_user.id, unit_type, count=1)
    await callback.answer(text, show_alert=not ok)
