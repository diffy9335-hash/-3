"""Война между игроками: /war <telegram_id>."""
from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.database import SessionLocal
from bot.models import User
from bot.services import battle_service

router = Router()


@router.message(Command("war"))
async def cmd_war(message: Message, command: CommandObject, bot: Bot) -> None:
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Использование: /war <telegram_id противника>")
        return
    defender_id = int(command.args.strip())
    async with SessionLocal() as session:
        attacker = await session.get(User, message.from_user.id)
        defender = await session.get(User, defender_id)
        if not attacker or attacker.nation_id is None:
            await message.answer("Сначала /start")
            return
        if not defender:
            await message.answer("❌ Противник не найден.")
            return
        battle = await battle_service.attack_player(session, message.from_user.id, defender_id)

    if battle is None:
        await message.answer("❌ У вас нет армии для атаки.")
        return

    icon = "🏆" if battle.status == "attacker_win" else "🛡️"
    await message.answer(
        f"{icon} **Бой с {defender.display_name()}** завершён!\n"
        f"Раундов: {battle.turns}\n\n" + "\n".join(battle.log),
        parse_mode="Markdown",
    )
    # Уведомление защитнику
    if defender.notifications_enabled:
        try:
            await bot.send_message(
                defender_id,
                f"⚠️ {attacker.display_name()} напал на вас!\n"
                f"{'💀 Вы отбили атаку!' if battle.status == 'defender_win' else '🏳️ Гарнизон разбит…'}\n"
                "Смотрите /battle_log",
            )
        except Exception:
            pass  # защитник заблокировал бота — лог сохранён в БД
