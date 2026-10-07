"""Профиль, настройки, статистика."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import SessionLocal
from bot.models import Nation, Resources, User

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if user is None or user.nation_id is None:
            await message.answer("Сначала зарегистрируйтесь: /start")
            return
        nation = await session.get(Nation, user.nation_id)
        res = await session.get(Resources, user.telegram_id)

    await message.answer(
        f"{nation.flag} **{user.display_name()}** — {nation.name}\n"
        f"🎖️ Уровень: {user.level} (XP: {user.exp})\n"
        f"🏛️ Правление: {user.government}\n"
        f"🕊️ Стабильность: {user.stability}%\n"
        f"⭐ Репутация: {user.reputation}\n"
        f"💵 Деньги: {res.money if res else 0}",
        parse_mode="Markdown",
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer("⚙️ Настройки: уведомления, приватность, язык — в разработке (этап 3).")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    async with SessionLocal() as session:
        from sqlalchemy import func, select
        from bot.models import Battle, User
        total = (await session.execute(select(func.count(User.telegram_id)))).scalar_one()
        wins = (await session.execute(select(func.count(Battle.id)).where(
            Battle.attacker_id == message.from_user.id, Battle.status == "attacker_win"))).scalar_one()
    await message.answer(f"📊 В мире государств: {total}. Ваши победы: {wins}.")
