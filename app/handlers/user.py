from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.keyboards import FAQS, FAQChoice, HandoffAction, faq_keyboard, handoff_keyboard
from app.models import DecisionType, SupportDecision
from app.services.answer_service import SupportService


router = Router(name="user")


def format_decision(decision: SupportDecision) -> str:
    if decision.decision is DecisionType.HANDOFF:
        return (
            "Уверенного ответа в базе знаний нет. Я не буду додумывать — "
            "обращение передано человеку."
            f"\n\nУверенность: <code>{decision.confidence:.2f}</code>"
        )
    return (
        f"{escape(decision.answer or '')}\n\n"
        f"Источник: <code>{escape(decision.source or '')}</code>\n"
        f"Уверенность: <code>{decision.confidence:.2f}</code>"
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Задайте вопрос о цифровых услугах или выберите частый вопрос.",
        reply_markup=faq_keyboard(),
    )


@router.callback_query(FAQChoice.filter())
async def answer_faq(query: CallbackQuery, callback_data: FAQChoice, support_service: SupportService) -> None:
    question = FAQS.get(callback_data.code)
    if question is None:
        await query.answer("Вопрос не найден.", show_alert=True)
        return
    decision = await support_service.respond(question, query.from_user.id)
    await query.answer()
    if query.message:
        await query.message.answer(format_decision(decision), reply_markup=handoff_keyboard())


@router.callback_query(HandoffAction.filter())
async def request_human(query: CallbackQuery, support_service: SupportService, manager_chat_id: int) -> None:
    decision = await support_service.request_handoff(
        "Пользователь запросил консультацию человека", query.from_user.id
    )
    await query.answer("Передано человеку")
    await query.bot.send_message(
        manager_chat_id,
        f"Новое обращение #{decision.message_id or '—'} от пользователя <code>{query.from_user.id}</code>.",
    )
    if query.message:
        await query.message.answer("Менеджер получил обращение.")


@router.message()
async def answer_message(message: Message, support_service: SupportService, manager_chat_id: int) -> None:
    if not message.text:
        await message.answer("Отправьте вопрос текстом.")
        return
    decision = await support_service.respond(message.text, message.from_user.id)
    await message.answer(format_decision(decision), reply_markup=handoff_keyboard())
    if decision.decision is DecisionType.HANDOFF:
        await message.bot.send_message(
            manager_chat_id,
            f"Передача человеку #{decision.message_id or '—'}\n"
            f"Вопрос: {escape(decision.question)}\n"
            f"Категория: <code>{decision.category.value}</code>\n"
            f"Уверенность: <code>{decision.confidence:.2f}</code>",
        )
