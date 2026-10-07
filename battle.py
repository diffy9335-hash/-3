"""Война: атаки на NPC, лог боёв."""
from sqlalchemy import select

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.database import SessionLocal
from bot.keyboards.main_menu import npc_targets_keyboard
from bot.models import Battle, User
from bot.services import battle_service

router = Router()


@router.message(Command("attack"))
async def cmd_attack(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user or user.nation_id is None:
            await message.answer("Сначала /start")
            return
        army = await battle_service.get_army(session, message.from_user.id)
    if not army:
        await message.answer("❌ У вас нет армии! Наймите войска: /army")
        return
    await message.answer("🎯 Выберите цель для атаки:", reply_markup=npc_targets_keyboard())


@router.callback_query(F.data.startswith("attack:"))
async def attack_callback(callback: CallbackQuery) -> None:
    target = callback.data.split(":")[1]
    if target == "menu":
        await callback.message.edit_text("🎯 Выберите цель:", reply_markup=npc_targets_keyboard())
        return
    async with SessionLocal() as session:
        battle = await battle_service.attack_npc(session, callback.from_user.id, target)
    icon = "🏆" if battle.status == "attacker_win" else "💀"
    await callback.message.edit_text(
        f"{icon} Бой с **{battle.npc_name}** завершён!\n"
        f"Раундов: {battle.turns}\n\n" + "\n".join(battle.log),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(Command("battle_log"))
async def cmd_battle_log(message: Message) -> None:
    async with SessionLocal() as session:
        battles = (await session.execute(
            select(Battle).where(Battle.attacker_id == message.from_user.id)
            .order_by(Battle.id.desc()).limit(5))).scalars().all()
    if not battles:
        await message.answer("История боёв пуста.")
        return
    lines = ["📜 **Последние бои:**"]
    for b in battles:
        icon = "🏆" if b.status == "attacker_win" else "💀"
        lines.append(f"{icon} #{b.id} vs {b.npc_name or 'игрок'} — {b.turns} раундов")
    await message.answer("\n".join(lines), parse_mode="Markdown")
