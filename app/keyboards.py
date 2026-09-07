from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


FAQS = {
    "pricing": "Сколько стоит Telegram-бот?",
    "terms": "Какие сроки разработки?",
    "services": "Какие услуги доступны?",
    "support": "Есть ли поддержка после запуска?",
}


class FAQChoice(CallbackData, prefix="faq"):
    code: str


class HandoffAction(CallbackData, prefix="handoff"):
    action: str


def faq_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=question, callback_data=FAQChoice(code=code).pack())]
            for code, question in FAQS.items()
        ]
    )


def handoff_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Позвать человека", callback_data=HandoffAction(action="request").pack())]
        ]
    )

