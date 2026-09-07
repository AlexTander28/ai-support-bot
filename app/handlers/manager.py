from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import Database
from app.services.answer_service import SupportService


router = Router(name="manager")


def is_manager(message: Message, manager_ids: frozenset[int]) -> bool:
    return bool(message.from_user and message.from_user.id in manager_ids)


@router.message(Command("stats"))
async def show_stats(message: Message, support_service: SupportService, manager_ids: frozenset[int]) -> None:
    if not is_manager(message, manager_ids):
        await message.answer("Команда доступна только менеджеру.")
        return
    stats = await support_service.get_stats()
    await message.answer(
        "<b>Статистика поддержки</b>\n\n"
        f"Всего: {stats.total}\n"
        f"Автоответы: {stats.by_decision['answer']}\n"
        f"Передано человеку: {stats.by_decision['handoff']}"
    )


@router.message(Command("handoffs"))
async def list_handoffs(message: Message, database: Database, manager_ids: frozenset[int]) -> None:
    if not is_manager(message, manager_ids):
        await message.answer("Команда доступна только менеджеру.")
        return
    rows = await database.list_open_handoffs()
    if not rows:
        await message.answer("Открытых обращений нет.")
        return
    text = ["<b>Открытые обращения</b>"]
    for handoff_id, user_id, question, category, confidence, reason in rows:
        text.append(
            f"#{handoff_id} · пользователь <code>{user_id}</code>\n"
            f"{escape(question)}\n<code>{category} · {confidence:.2f} · {reason}</code>"
        )
    await message.answer("\n\n".join(text))


@router.message(Command("resolve"))
async def resolve_handoff(message: Message, database: Database, manager_ids: frozenset[int]) -> None:
    if not is_manager(message, manager_ids):
        await message.answer("Команда доступна только менеджеру.")
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: <code>/resolve номер комментарий</code>")
        return
    handoff_id = int(parts[1])
    if await database.resolve_handoff(handoff_id, parts[2]):
        await message.answer(f"Обращение #{handoff_id} закрыто.")
        return
    await message.answer(f"Открытое обращение #{handoff_id} не найдено.")
