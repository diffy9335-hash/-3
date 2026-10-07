"""Клавиатуры: reply-главное меню и inline-навигация."""
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config.constants import BUILDINGS, NATIONS, NPC_TARGETS, UNITS, GOVERNMENTS


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню из брифа: 3 ряда по 2 кнопки."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏛️ Государство"), KeyboardButton(text="💰 Экономика")],
            [KeyboardButton(text="⚔️ Армия"), KeyboardButton(text="🗺️ Карта")],
            [KeyboardButton(text="🤝 Дипломатия"), KeyboardButton(text="🔬 Наука")],
            [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел…",
    )


def nations_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, n in enumerate(NATIONS):
        b.button(text=f"{n['flag']} {n['name']}", callback_data=f"nation:{i}")
    b.adjust(2)
    return b.as_markup()


def buildings_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, spec in BUILDINGS.items():
        b.button(text=f"{spec['emoji']} {spec['name']}", callback_data=f"build:{key}")
    b.adjust(2)
    return b.as_markup()


def army_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, spec in UNITS.items():
        b.button(text=f"{spec['emoji']} {spec['name']}", callback_data=f"recruit:{key}")
    b.button(text="⚔️ В атаку!", callback_data="attack:menu")
    b.adjust(2)
    return b.as_markup()


def npc_targets_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, t in NPC_TARGETS.items():
        b.button(text=f"{t['emoji']} {t['name']} (сила {t['power']})", callback_data=f"attack:{key}")
    b.adjust(1)
    return b.as_markup()


def government_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, g in GOVERNMENTS.items():
        b.button(text=g["name"], callback_data=f"gov:{key}")
    b.adjust(2)
    return b.as_markup()


def top_keyboard(active: str) -> InlineKeyboardMarkup:
    """Переключатель вкладок рейтинга; активная вкладка помечена •."""
    tabs = [("res", "💰 Ресурсы"), ("army", "⚔️ Армия"), ("land", "🗺️ Земли"), ("ach", "🏅 Ачивки")]
    b = InlineKeyboardBuilder()
    for key, title in tabs:
        b.button(text=f"• {title}" if key == active else title, callback_data=f"top:{key}")
    b.adjust(2)
    return b.as_markup()
