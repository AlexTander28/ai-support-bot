from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from app.database import Database
from app.llm_client import CategoryClassifier
from app.models import Category, DecisionType, RetrievalMatch, SupportDecision, SupportStats


class Retriever(Protocol):
    def retrieve(self, question: str) -> RetrievalMatch: ...


class SupportService:
    def __init__(
        self,
        retriever: Retriever,
        threshold: float = 0.65,
        database: Database | None = None,
        classifier: CategoryClassifier | None = None,
    ) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.retriever = retriever
        self.threshold = threshold
        self.database = database
        self.classifier = classifier

    async def respond(self, question: str, user_id: int) -> SupportDecision:
        match = self.retriever.retrieve(question)
        category = match.category
        if category is Category.UNKNOWN and self.classifier is not None:
            category = await self.classifier.classify(question)

        reason: str | None = None
        if not match.source or not match.answer:
            reason = "missing_source" if match.confidence >= self.threshold else "low_confidence"
        elif match.confidence < self.threshold:
            reason = "low_confidence"

        decision = SupportDecision(
            question=question,
            category=category if reason is None else (category if category is not Category.UNKNOWN else Category.UNKNOWN),
            confidence=match.confidence,
            decision=DecisionType.ANSWER if reason is None else DecisionType.HANDOFF,
            answer=match.answer if reason is None else None,
            source=match.source,
            excerpt=match.excerpt,
            reason=reason,
        )
        return await self._log(user_id, decision)

    async def request_handoff(self, question: str, user_id: int) -> SupportDecision:
        decision = SupportDecision(
            question=question,
            category=Category.UNKNOWN,
            confidence=0.0,
            decision=DecisionType.HANDOFF,
            answer=None,
            source=None,
            excerpt=None,
            reason="requested_by_user",
        )
        return await self._log(user_id, decision)

    async def get_stats(self) -> SupportStats:
        if self.database is None:
            return SupportStats(0, {item.value: 0 for item in DecisionType}, {})
        return await self.database.get_stats()

    async def _log(self, user_id: int, decision: SupportDecision) -> SupportDecision:
        if self.database is None:
            return decision
        message_id = await self.database.log_decision(user_id, decision)
        return replace(decision, message_id=message_id)

