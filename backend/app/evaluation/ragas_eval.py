import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import settings


EVALUATION_DIR = Path(__file__).resolve().parent
SCORES_PATH = EVALUATION_DIR / "scores.json"


async def run_ragas_evaluation(test_queries: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from ragas.run_config import RunConfig
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_openai import ChatOpenAI

        dataset = Dataset.from_list(test_queries)
        evaluator_llm = LangchainLLMWrapper(
            ChatOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                model=settings.groq_model,
                temperature=0,
            )
        )
        evaluator_embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        )
        for metric in [faithfulness, answer_relevancy, context_precision, context_recall]:
            if hasattr(metric, "llm"):
                metric.llm = evaluator_llm
            if hasattr(metric, "embeddings"):
                metric.embeddings = evaluator_embeddings

        results = await asyncio.to_thread(
            evaluate,
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            run_config=RunConfig(timeout=240, max_retries=3, max_wait=30, max_workers=1),
            batch_size=1,
            raise_exceptions=False,
        )
        scores = getattr(results, "_scores_dict", None)
        if not scores:
            scores = {
                metric_name: results[metric_name]
                for metric_name in [
                    "faithfulness",
                    "answer_relevancy",
                    "context_precision",
                    "context_recall",
                ]
            }
        scores = {
            key: (None if value != value else float(value))
            for key, value in scores.items()
        }
        scores["status"] = "completed"
        SCORES_PATH.write_text(json.dumps(scores, indent=2), encoding="utf-8")
        return scores
    except Exception as exc:
        failure = {
            "status": "failed",
            "reason": str(exc),
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
        }
        SCORES_PATH.write_text(json.dumps(failure, indent=2), encoding="utf-8")
        return failure


def get_saved_scores() -> dict[str, Any]:
    try:
        return json.loads(SCORES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "status": "not_run",
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
        }
    except Exception as exc:
        raise RuntimeError(f"Unable to read evaluation scores: {exc}") from exc
