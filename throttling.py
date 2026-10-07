"""Антиспам: не больше N апдейтов в секунду на пользователя."""
import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self._last: dict[int, float] = defaultdict(float)

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            now = time.monotonic()
            user_id = event.from_user.id
            if now - self._last[user_id] < self.rate_limit:
                await event.answer("⏳ Не так быстро! Подождите секунду.")
                return
            self._last[user_id] = now
        return await handler(event, data)
