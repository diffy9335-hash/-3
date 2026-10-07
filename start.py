"""Регистрация: /start, выбор нации."""
from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.config.constants import NATIONS
from bot.database import SessionLocal
from bot.keyboards.main_menu import main_menu, nations_keyboard
from bot.models import Nation, User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                nickname=message.from_user.first_name or "Командир",
            )
            session.add(user)
            await session.commit()
            await message.answer(
                "👋 Добро пожаловать в **«Военную стратегию»**!\n"
                "Выберите нацию для своего государства:",
                parse_mode="Markdown", reply_markup=nations_keyboard(),
            )
            return

        nation = await session.get(Nation, user.nation_id) if user.nation_id else None
        if nation is None:
            await message.answer("Выберите нацию:", reply_markup=nations_keyboard())
            return

    await message.answer(
        f"С возвращением, {user.display_name()}! {nation.flag}\nГлавное меню:",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data.startswith("nation:"))
async def choose_nation(callback: CallbackQuery, bot: Bot) -> None:
    idx = int(callback.data.split(":")[1])
    spec = NATIONS[idx]

    async with SessionLocal() as session:
        user = await session.get(User, callback.from_user.id)
        if user is None:
            await callback.answer("Сначала /start", show_alert=True)
            return
        if user.nation_id is not None:
            await callback.answer("Нацию нельзя сменить!", show_alert=True)
            return

        nation = (await session.execute(
            select(Nation).where(Nation.code == spec["code"]))).scalar_one_or_none()
        if nation is None:
            await callback.answer("Нация недоступна, попробуйте позже.", show_alert=True)
            return
        user.nation_id = nation.id
        await session.commit()

    await callback.message.edit_text(
        f"{spec['flag']} Вы основали государство **{spec['name']}**!\n"
        f"Бонусы: 💰+{spec['bonus_economy']}% ⚔️+{spec['bonus_army']}% "
        f"🔬+{spec['bonus_science']}% 🕊️+{spec['bonus_stability']}%",
        parse_mode="Markdown",
    )
    await bot.send_message(callback.from_user.id, "Главное меню:", reply_markup=main_menu())
    await callback.answer()
