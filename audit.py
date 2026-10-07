"""Запись всех команд и действий в audit_log (anti-cheat, инциденты)."""
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.database import SessionLocal
from bot.models import AuditLog


class AuditMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            if isinstance(event, Message):
                uid, action, payload = event.from_user.id, "command", {"text": event.text}
            elif isinstance(event, CallbackQuery):
                uid, action, payload = event.from_user.id, "callback", {"data": event.data}
            else:
                return await handler(event, data)
            async with SessionLocal() as session:
                session.add(AuditLog(user_id=uid, action=action, payload=payload))
                await session.commit()
        except Exception:
            pass  # аудит не должен ломать обработку
        return await handler(event, data)
