from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import ConfigurationError, Settings
from app.database import Database
from app.handlers import manager_router, user_router
from app.knowledge_base import KnowledgeBase
from app.llm_client import OpenAICompatibleClassifier
from app.services.answer_service import SupportService


async def run() -> None:
    settings = Settings.from_env()
    database = Database(settings.database_path)
    await database.initialize()
    knowledge_base = KnowledgeBase.from_json(settings.knowledge_base_path)
    classifier = None
    if settings.llm_api_key:
        classifier = OpenAICompatibleClassifier(
            settings.llm_api_key, settings.llm_base_url, settings.llm_model
        )
    service = SupportService(
        knowledge_base, settings.confidence_threshold, database, classifier
    )
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(
        support_service=service,
        database=database,
        manager_chat_id=settings.manager_chat_id,
        manager_ids=settings.manager_ids,
    )
    dispatcher.include_router(manager_router)
    dispatcher.include_router(user_router)
    await dispatcher.start_polling(bot)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    try:
        asyncio.run(run())
    except ConfigurationError as error:
        logging.error("Configuration error: %s", error)
        return 2
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

