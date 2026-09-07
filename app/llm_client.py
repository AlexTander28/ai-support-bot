from __future__ import annotations

from typing import Protocol

import httpx

from app.models import Category


class CategoryClassifier(Protocol):
    async def classify(self, question: str) -> Category: ...


class OpenAICompatibleClassifier:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = client or httpx.AsyncClient(timeout=15)

    async def classify(self, question: str) -> Category:
        allowed = ", ".join(item.value for item in Category)
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": f"Return one category only: {allowed}."},
                        {"role": "user", "content": question},
                    ],
                },
            )
            response.raise_for_status()
            value = response.json()["choices"][0]["message"]["content"].strip().casefold()
            return Category(value)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            return Category.UNKNOWN

