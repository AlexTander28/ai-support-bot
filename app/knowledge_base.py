from __future__ import annotations

import json
import re
from pathlib import Path

from app.models import Category, KnowledgeEntry, RetrievalMatch


TOKEN_RE = re.compile(r"[a-zа-я0-9]+", re.IGNORECASE)
STOP_WORDS = {
    "а", "в", "вы", "для", "и", "из", "к", "как", "ли", "на", "по",
    "про", "с", "у", "это", "я", "мне", "можно", "нужен", "нужно",
}


def normalize(text: str) -> str:
    return " ".join(TOKEN_RE.findall(text.casefold().replace("ё", "е")))


def tokens(text: str) -> set[str]:
    return {token for token in normalize(text).split() if token not in STOP_WORDS}


class KnowledgeBase:
    def __init__(self, entries: tuple[KnowledgeEntry, ...]) -> None:
        if not entries:
            raise ValueError("Knowledge base must contain at least one entry")
        self.entries = entries

    @classmethod
    def from_json(cls, path: Path) -> "KnowledgeBase":
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = tuple(
            KnowledgeEntry(
                entry_id=item["id"],
                category=Category(item["category"]),
                title=item["title"],
                source=item["source"],
                answer=item["answer"],
                keywords=tuple(item["keywords"]),
                examples=tuple(item["examples"]),
            )
            for item in payload["entries"]
        )
        return cls(entries)

    def retrieve(self, question: str) -> RetrievalMatch:
        query_tokens = tokens(question)
        normalized_question = normalize(question)
        if not query_tokens:
            return self._unknown()

        best_entry: KnowledgeEntry | None = None
        best_score = 0.0
        for entry in self.entries:
            phrase_score = max(
                (self._token_coverage(query_tokens, tokens(example)) for example in entry.examples),
                default=0.0,
            )
            entry_tokens = tokens(" ".join((*entry.examples, *entry.keywords, entry.title)))
            query_coverage = len(query_tokens & entry_tokens) / len(query_tokens)
            keyword_hit = float(any(normalize(keyword) in normalized_question for keyword in entry.keywords))
            score = min(1.0, 0.55 * phrase_score + 0.30 * query_coverage + 0.15 * keyword_hit)
            if score > best_score:
                best_entry, best_score = entry, score

        if best_entry is None or best_score < 0.20:
            return self._unknown()
        return RetrievalMatch(
            category=best_entry.category,
            confidence=round(best_score, 2),
            answer=best_entry.answer,
            source=best_entry.source,
            excerpt=best_entry.title,
        )

    @staticmethod
    def _token_coverage(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / max(len(left), len(right))

    @staticmethod
    def _unknown() -> RetrievalMatch:
        return RetrievalMatch(Category.UNKNOWN, 0.0, None, None, None)

