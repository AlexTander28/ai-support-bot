from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Category(StrEnum):
    PRICING = "pricing"
    TERMS = "terms"
    SERVICES = "services"
    PAYMENT = "payment"
    SUPPORT = "support"
    UNKNOWN = "unknown"


class DecisionType(StrEnum):
    ANSWER = "answer"
    HANDOFF = "handoff"


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    entry_id: str
    category: Category
    title: str
    source: str
    answer: str
    keywords: tuple[str, ...]
    examples: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetrievalMatch:
    category: Category
    confidence: float
    answer: str | None
    source: str | None
    excerpt: str | None


@dataclass(frozen=True, slots=True)
class SupportDecision:
    question: str
    category: Category
    confidence: float
    decision: DecisionType
    answer: str | None
    source: str | None
    excerpt: str | None
    reason: str | None
    message_id: int | None = None


@dataclass(frozen=True, slots=True)
class SupportStats:
    total: int
    by_decision: dict[str, int]
    by_category: dict[str, int]

