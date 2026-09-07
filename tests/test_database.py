from __future__ import annotations

import pytest

from app.database import Database
from app.models import DecisionType
from app.services.answer_service import SupportService


@pytest.mark.asyncio
async def test_decisions_are_logged_and_counted(tmp_path, knowledge_base) -> None:
    database = Database(tmp_path / "support.sqlite3")
    await database.initialize()
    service = SupportService(knowledge_base, threshold=0.65, database=database)

    await service.respond("Какие услуги вы делаете?", user_id=201)
    await service.respond("Подберёте музыку для ролика?", user_id=202)
    await service.request_handoff("Хочу поговорить с человеком", user_id=203)
    stats = await service.get_stats()

    assert stats.total == 3
    assert stats.by_decision[DecisionType.ANSWER.value] == 1
    assert stats.by_decision[DecisionType.HANDOFF.value] == 2
    assert stats.by_category["services"] == 1
    assert stats.by_category["unknown"] == 2


@pytest.mark.asyncio
async def test_manager_can_resolve_open_handoff(tmp_path, knowledge_base) -> None:
    database = Database(tmp_path / "support.sqlite3")
    await database.initialize()
    service = SupportService(knowledge_base, threshold=0.65, database=database)

    await service.request_handoff("Нужна консультация человека", user_id=204)
    handoff_id = (await database.list_open_handoffs())[0][0]

    resolved = await database.resolve_handoff(handoff_id, "Ответ отправлен клиенту")

    assert resolved is True
    assert await database.list_open_handoffs() == []
    assert await database.resolve_handoff(handoff_id, "Повторное закрытие") is False
