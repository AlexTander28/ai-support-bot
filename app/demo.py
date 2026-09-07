from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.database import Database
from app.knowledge_base import KnowledgeBase
from app.models import DecisionType
from app.services.answer_service import SupportService


QUESTIONS = (
    "Сколько стоит Telegram-бот?",
    "Какие сроки разработки?",
    "Какие услуги вы делаете?",
    "Как оплатить проект?",
    "Есть ли поддержка после запуска?",
    "Настроите дрон для съёмки свадьбы?",
    "Можете гарантировать миллион продаж?",
    "Вы делаете CRM и Excel-отчёты?",
    "Можно оплатить через бота?",
    "Подберёте музыку для ролика?",
)


async def build_demo(database_path: Path, knowledge_base_path: Path, report_path: Path) -> dict:
    database = Database(database_path)
    await database.initialize()
    service = SupportService(KnowledgeBase.from_json(knowledge_base_path), 0.65, database)
    samples = []
    for index, question in enumerate(QUESTIONS, start=1):
        decision = await service.respond(question, user_id=7000 + index)
        samples.append(
            {
                "question": question,
                "category": decision.category.value,
                "confidence": decision.confidence,
                "decision": decision.decision.value,
                "answer": decision.answer,
                "source": decision.source,
                "reason": decision.reason,
            }
        )
    stats = await service.get_stats()
    report = {
        "synthetic": True,
        "threshold": 0.65,
        "total": stats.total,
        "answers": stats.by_decision[DecisionType.ANSWER.value],
        "handoffs": stats.by_decision[DecisionType.HANDOFF.value],
        "by_category": stats.by_category,
        "samples": samples,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the deterministic support bot demo")
    parser.add_argument("--database", type=Path, default=Path("data/support.sqlite3"))
    parser.add_argument("--knowledge-base", type=Path, default=Path("knowledge_base/faq.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/support_demo.json"))
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()
    if args.reset:
        args.database.unlink(missing_ok=True)
    report = await build_demo(args.database, args.knowledge_base, args.report)
    print(f"Demo created | total={report['total']} | answers={report['answers']} | handoffs={report['handoffs']}")


if __name__ == "__main__":
    asyncio.run(async_main())

