"""Блокировка забаненных игроков (админы — вне бана)."""
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.config.settings import settings
from bot.database import SessionLocal
from bot.models import User


class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None or user.id in settings.ADMIN_IDS:
            return await handler(event, data)

        async with SessionLocal() as session:
            db_user = await session.get(User, user.id)
        if db_user is None or not db_user.is_banned:
            return await handler(event, data)

        text = "⛔ Вы заблокированы администрацией." + (
            f"\nПричина: {db_user.ban_reason}" if db_user.ban_reason else "")
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(text)
        return None
