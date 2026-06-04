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
from app.llm import llm
from app.reranker import reranker
from app.services.rag_service import generate_response
from app.services.vector_store import hybrid_retriever


def env_flag(name: str, default: bool) -> bool:
    try:
        return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}
    except Exception:
        return default


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


async def generate_quota_safe_sample(question: str, ground_truth: str) -> dict:
    try:
        top_k = int(os.getenv("EVAL_TOP_K", "3"))
        context_char_limit = int(os.getenv("EVAL_CONTEXT_CHAR_LIMIT", "600"))
        candidates = await hybrid_retriever.retrieve(question, top_k=20)
        docs = await reranker.rerank(question, candidates, top_k=top_k)
        if env_flag("EVAL_GENERATE_WITH_LLM", False):
            answer = await llm.generate(question, context=docs)
        else:
            if not docs:
                answer = "I could not find relevant products in the current catalog."
            else:
                product_lines = [
                    (
                        f"{index}. {doc.get('title')}: "
                        f"{doc.get('description') or doc.get('text', '')[:180]}"
                    )
                    for index, doc in enumerate(docs, start=1)
                ]
                answer = (
                    "Based on the retrieved catalog documents, the best matches are:\n"
                    + "\n".join(product_lines)
                )
        return {
            "question": question,
            "answer": answer,
            "contexts": [
                (product.get("text", "") or "")[:context_char_limit] for product in docs
            ],
            "ground_truth": ground_truth,
        }
    except Exception as exc:
        raise RuntimeError(f"Unable to generate quota-safe evaluation sample: {exc}") from exc


async def main() -> None:
    try:
        test_path = Path(__file__).resolve().parent / "test_queries.json"
        tests = json.loads(test_path.read_text(encoding="utf-8"))
        safe_mode = env_flag("EVAL_SAFE_MODE", True)
        limit = int(os.getenv("EVAL_LIMIT", "3" if safe_mode else "0"))
        if limit > 0:
            tests = tests[:limit]
        await prepare_retriever()
        samples = []
        for test in tests:
            if safe_mode:
                samples.append(
                    await generate_quota_safe_sample(
                        test["question"], test["ground_truth"]
                    )
                )
            else:
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
        scores = await run_ragas_evaluation(
            samples,
            metadata={
                "safe_mode": safe_mode,
                "query_count": len(samples),
                "top_k": int(os.getenv("EVAL_TOP_K", "3")),
                "generated_with_llm": env_flag("EVAL_GENERATE_WITH_LLM", False),
                "context_char_limit": int(os.getenv("EVAL_CONTEXT_CHAR_LIMIT", "600")),
            },
        )
        print(json.dumps(scores, indent=2))
    except Exception as exc:
        raise RuntimeError(f"Evaluation run failed: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
