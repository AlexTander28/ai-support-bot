from __future__ import annotations

import json

import pytest

from app.demo import build_demo


@pytest.mark.asyncio
async def test_demo_contains_answer_and_handoff_routes(tmp_path, knowledge_base_path) -> None:
    report_path = tmp_path / "support_demo.json"

    await build_demo(tmp_path / "support.sqlite3", knowledge_base_path, report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["synthetic"] is True
    assert report["total"] == 10
    assert report["answers"] >= 4
    assert report["handoffs"] >= 2
    assert {item["decision"] for item in report["samples"]} == {"answer", "handoff"}

