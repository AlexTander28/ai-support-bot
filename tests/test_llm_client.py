from __future__ import annotations

import httpx
import pytest

from app.llm_client import OpenAICompatibleClassifier
from app.models import Category


@pytest.mark.asyncio
async def test_external_classifier_accepts_known_category_without_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": "pricing"}}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    classifier = OpenAICompatibleClassifier("test-key", "https://example.test/v1", "test-model", client)

    assert await classifier.classify("Сколько стоит бот?") is Category.PRICING
    await client.aclose()


@pytest.mark.asyncio
async def test_external_classifier_rejects_unexpected_output() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"message": {"content": "make_up_price"}}]})
    )
    client = httpx.AsyncClient(transport=transport)
    classifier = OpenAICompatibleClassifier("test-key", "https://example.test/v1", "test-model", client)

    assert await classifier.classify("Назови цену") is Category.UNKNOWN
    await client.aclose()

