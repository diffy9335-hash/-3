"""Агрегация роутеров хэндлеров."""
from aiogram import Router

from bot.handlers import admin, army, battle, economy, map, profile, start, top, war


def get_handlers_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(profile.router)
    router.include_router(economy.router)
    router.include_router(army.router)
    router.include_router(battle.router)
    router.include_router(map.router)
    router.include_router(war.router)
    router.include_router(top.router)
    router.include_router(admin.router)
    return router
