import asyncio
import json
import os
from pathlib import Path

if os.getenv("EVAL_DISABLE_TRACING", "true").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

from sqlalchemy import select

from app.evaluation.ragas_eval import run_ragas_evaluation
from app import models
from app.database import AsyncSessionLocal, init_db
from app.services.rag_service import generate_response
from app.services.vector_store import hybrid_retriever


async def prepare_retriever() -> None:
    try:
        await init_db()
        async with AsyncSessionLocal() as db:
            products = list((await db.scalars(select(models.Product))).all())
            await hybrid_retriever.sync_products(
                [
                    {
                        "id": product.id,
                        "title": product.title,
                        "price": product.price,
                        "description": product.description or "",
                        "features": product.features or [],
                        "image_url": product.image_url,
                        "category": product.category,
                        "url": product.url,
                    }
                    for product in products
                ]
            )
    except Exception as exc:
        raise RuntimeError(f"Unable to prepare retriever for evaluation: {exc}") from exc


async def main() -> None:
    try:
        test_path = Path(__file__).resolve().parent / "test_queries.json"
        tests = json.loads(test_path.read_text(encoding="utf-8"))
        limit = int(os.getenv("EVAL_LIMIT", "0"))
        if limit > 0:
            tests = tests[:limit]
        await prepare_retriever()
        samples = []
        for test in tests:
            result = await generate_response(test["question"])
            samples.append(
                {
                    "question": test["question"],
                    "answer": result["response"],
                    "contexts": [
                        product.get("text", "") for product in result.get("products", [])
                    ],
                    "ground_truth": test["ground_truth"],
                }
            )
        scores = await run_ragas_evaluation(samples)
        print(json.dumps(scores, indent=2))
    except Exception as exc:
        raise RuntimeError(f"Evaluation run failed: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
