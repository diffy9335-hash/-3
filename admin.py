"""Админ-панель (только ADMIN_IDS): выдача ресурсов, бан/разбан, просмотр audit_log.

/admin                                   — справка и сводка
/admin give <id> <ресурс> <кол-во>       — выдать (отрицательное — забрать, не ниже 0)
/admin ban <id> [причина]                — забанить
/admin unban <id>                        — разбанить
/admin log [id|all] [N]                  — последние записи audit_log
"""
from datetime import timezone
from html import escape
import json

from aiogram import Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config.constants import ADMIN_LOG_DEFAULT, ADMIN_LOG_MAX, ADMIN_MAX_GRANT, ADMIN_RESOURCES
from bot.config.settings import settings
from bot.database import SessionLocal
from bot.models import AuditLog, User
from bot.services.economy_service import get_or_create_resources

router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in settings.ADMIN_IDS


# Не-админам /admin не отвечаем вовсе: фильтр не пропускает апдейт к хэндлеру.
router.message.filter(IsAdmin())

HELP = (
    "🛠️ <b>Админ-панель</b>\n"
    "Игроков: {users} · в бане: {banned} · записей в audit_log: {logs}\n\n"
    "<code>/admin give &lt;id&gt; &lt;ресурс&gt; &lt;кол-во&gt;</code> — выдать (минус — забрать)\n"
    "Ресурсы: " + ", ".join(ADMIN_RESOURCES) + "\n"
    "<code>/admin ban &lt;id&gt; [причина]</code> — забанить\n"
    "<code>/admin unban &lt;id&gt;</code> — разбанить\n"
    f"<code>/admin log [id|all] [N]</code> — audit_log (по умолчанию {ADMIN_LOG_DEFAULT}, максимум {ADMIN_LOG_MAX})"
)


def _log(session, admin_id: int, action: str, payload: dict) -> None:
    session.add(AuditLog(user_id=admin_id, action=action, payload=payload))


@router.message(Command("admin"))
async def cmd_admin(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    sub = args[0].lower() if args else ""
    if sub == "give":
        await _give(message, args[1:])
    elif sub == "ban":
        await _ban(message, args[1:], banned=True)
    elif sub == "unban":
        await _ban(message, args[1:], banned=False)
    elif sub == "log":
        await _audit(message, args[1:])
    else:
        async with SessionLocal() as session:
            users = (await session.execute(select(func.count(User.telegram_id)))).scalar_one()
            banned = (await session.execute(
                select(func.count(User.telegram_id)).where(User.is_banned.is_(True)))).scalar_one()
            logs = (await session.execute(select(func.count(AuditLog.id)))).scalar_one()
        await message.answer(HELP.format(users=users, banned=banned, logs=logs), parse_mode="HTML")


async def _give(message: Message, args: list[str]) -> None:
    try:
        target, resource, amount = int(args[0]), args[1].lower(), int(args[2])
    except (IndexError, ValueError):
        await message.answer("Использование: /admin give <id> <ресурс> <кол-во>")
        return
    if resource not in ADMIN_RESOURCES:
        await message.answer("❌ Неизвестный ресурс. Доступны: " + ", ".join(ADMIN_RESOURCES))
        return
    if amount == 0 or abs(amount) > ADMIN_MAX_GRANT:
        await message.answer(f"❌ Количество: от 1 до {ADMIN_MAX_GRANT:,} (можно со знаком минус).")
        return

    async with SessionLocal() as session:
        user = await session.get(User, target)
        if user is None:
            await message.answer("❌ Игрок не найден.")
            return
        res = await get_or_create_resources(session, target)
        before = getattr(res, resource)
        after = max(0, before + amount)
        setattr(res, resource, after)
        _log(session, message.from_user.id, "admin_give",
             {"target": target, "resource": resource, "amount": amount, "before": before, "after": after})
        await session.commit()
        name = escape(user.display_name())
    await message.answer(f"✅ {name} ({target}): {resource} {before:,} → {after:,}", parse_mode="HTML")


async def _ban(message: Message, args: list[str], banned: bool) -> None:
    if not args or not args[0].lstrip("-").isdigit():
        await message.answer("Использование: /admin ban <id> [причина]" if banned
                             else "Использование: /admin unban <id>")
        return
    target = int(args[0])
    if target in settings.ADMIN_IDS:
        await message.answer("❌ Админов банить нельзя.")
        return
    reason = " ".join(args[1:])[:255] or None

    async with SessionLocal() as session:
        user = await session.get(User, target)
        if user is None:
            await message.answer("❌ Игрок не найден.")
            return
        user.is_banned = banned
        user.ban_reason = reason if banned else None
        _log(session, message.from_user.id, "admin_ban" if banned else "admin_unban",
             {"target": target, "reason": reason})
        await session.commit()
        name = escape(user.display_name())
    if banned:
        await message.answer(f"⛔ {name} ({target}) забанен." + (f"\nПричина: {escape(reason)}" if reason else ""),
                             parse_mode="HTML")
    else:
        await message.answer(f"✅ {name} ({target}) разбанен.", parse_mode="HTML")


async def _audit(message: Message, args: list[str]) -> None:
    target: int | None = None
    limit = ADMIN_LOG_DEFAULT
    try:
        if args and args[0].lower() != "all":
            target = int(args[0])
        if len(args) > 1:
            limit = int(args[1])
    except ValueError:
        await message.answer("Использование: /admin log [id|all] [N]")
        return
    limit = max(1, min(limit, ADMIN_LOG_MAX))

    async with SessionLocal() as session:
        q = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        if target is not None:
            q = q.where(AuditLog.user_id == target)
        rows = (await session.execute(q)).scalars().all()
    if not rows:
        await message.answer("audit_log пуст.")
        return

    head = f"📜 <b>audit_log</b> (UTC), {'игрок ' + str(target) if target else 'все'}:\n"
    body: list[str] = []
    size = len(head)
    for r in rows:
        ts = r.created_at.astimezone(timezone.utc).strftime("%d.%m %H:%M:%S") if r.created_at else "?"
        payload = json.dumps(r.payload, ensure_ascii=False)
        if len(payload) > 70:
            payload = payload[:70] + "…"
        line = f"#{r.id} {ts} u{r.user_id} {r.action} {payload}"
        if size + len(line) + 20 > 3900:   # лимит Telegram — 4096 символов
            body.append("…")
            break
        body.append(line)
        size += len(line) + 1
    await message.answer(head + "<pre>" + escape("\n".join(body)) + "</pre>", parse_mode="HTML")
