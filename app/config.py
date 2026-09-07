from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required runtime settings are absent or unsafe."""


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    manager_chat_id: int
    manager_ids: frozenset[int]
    database_path: Path
    knowledge_base_path: Path
    confidence_threshold: float
    llm_api_key: str | None
    llm_base_url: str
    llm_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token == "replace_with_botfather_token":
            raise ConfigurationError("BOT_TOKEN не задан. Скопируйте .env.example в .env.")
        try:
            chat_id = int(os.getenv("MANAGER_CHAT_ID", "0"))
            manager_ids = frozenset(
                int(value.strip()) for value in os.getenv("MANAGER_IDS", "").split(",") if value.strip()
            )
            threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
        except ValueError as error:
            raise ConfigurationError("Проверьте MANAGER_CHAT_ID, MANAGER_IDS и CONFIDENCE_THRESHOLD.") from error
        if chat_id == 0 or not manager_ids:
            raise ConfigurationError("Добавьте MANAGER_CHAT_ID и хотя бы один MANAGER_IDS.")
        if not 0 <= threshold <= 1:
            raise ConfigurationError("CONFIDENCE_THRESHOLD должен быть от 0 до 1.")
        return cls(
            bot_token=token,
            manager_chat_id=chat_id,
            manager_ids=manager_ids,
            database_path=Path(os.getenv("DATABASE_PATH", "data/support.sqlite3")),
            knowledge_base_path=Path(os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base/faq.json")),
            confidence_threshold=threshold,
            llm_api_key=os.getenv("LLM_API_KEY", "").strip() or None,
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("LLM_MODEL", "replace_with_model_name"),
        )
