"""Рейтинги: /top — ресурсы, армия, территории, достижения."""
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config.constants import TOP_LIMIT
from bot.database import SessionLocal
from bot.keyboards.main_menu import top_keyboard
from bot.services import rating_service as rs

router = Router()
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
TITLES = {**{k: v[0] for k, v in rs.BOARDS.items()}, "ach": "🏅 Достижения"}


def render(stats: dict, board: str, viewer_id: int) -> str:
    top, my_rank, me = rs.build_board(stats, board, viewer_id, TOP_LIMIT)
    lines = [f"🏆 <b>Рейтинг — {TITLES[board]}</b>", ""]

    if board == "ach":
        total = len(rs.ACHIEVEMENTS)
        if me:
            lines.append(f"<b>Ваши достижения ({rs.ach_count(me)}/{total}):</b>")
            for a in rs.achievements_for(me):
                if a["done"]:
                    lines.append(f"✅ {a['emoji']} {a['name']} — {a['desc']}")
                else:
                    lines.append(f"🔒 {a['emoji']} {a['name']} — {a['desc']} ({a['current']}/{a['goal']})")
            lines.append("")
        else:
            lines += ["Зарегистрируйтесь через /start, чтобы получать достижения.", ""]
        lines.append("<b>Больше всего достижений:</b>")

    if not top:
        lines.append("Пока пусто.")
    for i, s in enumerate(top, 1):
        value = f"{rs.ach_count(s)}/{len(rs.ACHIEVEMENTS)} 🏅" if board == "ach" else rs.BOARDS[board][2](s)
        you = " ← вы" if s.user_id == viewer_id else ""
        lines.append(f"{MEDALS.get(i, f'{i}.')} {s.flag} {escape(s.name)} — {value}{you}")

    if my_rank and my_rank > TOP_LIMIT and me:
        value = f"{rs.ach_count(me)}/{len(rs.ACHIEVEMENTS)} 🏅" if board == "ach" else rs.BOARDS[board][2](me)
        lines += ["…", f"{my_rank}. {me.flag} {escape(me.name)} — {value} ← вы"]
    return "\n".join(lines)


async def _show(message: Message, board: str, viewer_id: int, edit: bool) -> None:
    async with SessionLocal() as session:
        stats = await rs.collect_stats(session)
    text = render(stats, board, viewer_id)
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=top_keyboard(board))
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=top_keyboard(board))


@router.message(Command("top"))
@router.message(F.text == "🏆 Топ")
async def cmd_top(message: Message) -> None:
    await _show(message, "res", message.from_user.id, edit=False)


@router.callback_query(F.data.startswith("top:"))
async def top_tab(callback: CallbackQuery) -> None:
    board = callback.data.split(":")[1]
    if board not in TITLES:
        await callback.answer()
        return
    try:
        await _show(callback.message, board, callback.from_user.id, edit=True)
    except TelegramBadRequest:
        pass  # «message is not modified» при повторном нажатии на ту же вкладку
    await callback.answer()
