from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge_base import KnowledgeBase


@pytest.fixture
def knowledge_base_path() -> Path:
    return Path(__file__).parents[1] / "knowledge_base" / "faq.json"


@pytest.fixture
def knowledge_base(knowledge_base_path: Path) -> KnowledgeBase:
    return KnowledgeBase.from_json(knowledge_base_path)

