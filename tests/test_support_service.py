from __future__ import annotations

import pytest

from app.models import Category, DecisionType, RetrievalMatch
from app.services.answer_service import SupportService


@pytest.mark.asyncio
async def test_known_pricing_question_returns_sourced_answer(knowledge_base) -> None:
    service = SupportService(knowledge_base, threshold=0.65)

    decision = await service.respond("Сколько стоит Telegram-бот?", user_id=101)

    assert decision.decision is DecisionType.ANSWER
    assert decision.category is Category.PRICING
    assert decision.confidence >= 0.65
    assert decision.source == "База знаний / Стоимость / Telegram-бот"
    assert "5 000" in decision.answer


@pytest.mark.asyncio
async def test_unknown_question_is_handed_off_without_answer(knowledge_base) -> None:
    service = SupportService(knowledge_base, threshold=0.65)

    decision = await service.respond("Настроите дрон для съёмки свадьбы?", user_id=102)

    assert decision.decision is DecisionType.HANDOFF
    assert decision.category is Category.UNKNOWN
    assert decision.answer is None
    assert decision.reason == "low_confidence"


class StubRetriever:
    def __init__(self, match: RetrievalMatch) -> None:
        self.match = match

    def retrieve(self, question: str) -> RetrievalMatch:
        return self.match


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("confidence", "expected"),
    [(0.64, DecisionType.HANDOFF), (0.65, DecisionType.ANSWER)],
)
async def test_threshold_boundary_is_inclusive(confidence, expected) -> None:
    match = RetrievalMatch(
        category=Category.SERVICES,
        confidence=confidence,
        answer="Подтверждённый ответ",
        source="База знаний / Услуги",
        excerpt="Подтверждённый фрагмент",
    )
    service = SupportService(StubRetriever(match), threshold=0.65)

    decision = await service.respond("Вопрос", user_id=103)

    assert decision.decision is expected
    assert (decision.answer is not None) is (expected is DecisionType.ANSWER)


@pytest.mark.asyncio
async def test_answer_without_source_is_handed_off() -> None:
    match = RetrievalMatch(
        category=Category.PRICING,
        confidence=0.99,
        answer="Ответ без доказательства",
        source=None,
        excerpt=None,
    )
    service = SupportService(StubRetriever(match), threshold=0.65)

    decision = await service.respond("Вопрос", user_id=104)

    assert decision.decision is DecisionType.HANDOFF
    assert decision.answer is None
    assert decision.reason == "missing_source"


@pytest.mark.asyncio
async def test_manual_handoff_never_returns_automatic_answer(knowledge_base) -> None:
    service = SupportService(knowledge_base, threshold=0.65)

    decision = await service.request_handoff("Нужен человек", user_id=105)

    assert decision.decision is DecisionType.HANDOFF
    assert decision.answer is None
    assert decision.reason == "requested_by_user"

