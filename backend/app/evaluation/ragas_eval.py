import asyncio
import json
import math
from pathlib import Path
from typing import Any

from app.config import settings


EVALUATION_DIR = Path(__file__).resolve().parent
SCORES_PATH = EVALUATION_DIR / "scores.json"
DEFAULT_EVAL_JUDGE_MODEL = "llama-3.1-8b-instant"


def _score_value(value: Any) -> float | None:
    try:
        if isinstance(value, list):
            numeric = [
                float(item)
                for item in value
                if item is not None and not math.isnan(float(item))
            ]
            return sum(numeric) / len(numeric) if numeric else None
        numeric_value = float(value)
        return None if math.isnan(numeric_value) else numeric_value
    except Exception:
        return None


def _is_rate_limit_error(message: str) -> bool:
    try:
        lowered = message.lower()
        return any(
            marker in lowered
            for marker in ["rate limit", "rate_limit", "quota", "429", "tokens per day"]
        )
    except Exception:
        return False


async def run_ragas_evaluation(
    test_queries: list[dict[str, Any]], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        import os

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
        judge_model = os.getenv("EVAL_JUDGE_MODEL", DEFAULT_EVAL_JUDGE_MODEL)
        evaluator_llm = LangchainLLMWrapper(
            ChatOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                model=judge_model,
                temperature=0,
                max_tokens=int(os.getenv("EVAL_JUDGE_MAX_TOKENS", "1024")),
                timeout=int(os.getenv("EVAL_JUDGE_TIMEOUT", "120")),
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
            run_config=RunConfig(
                timeout=int(os.getenv("EVAL_RAGAS_TIMEOUT", "240")),
                max_retries=int(os.getenv("EVAL_RAGAS_MAX_RETRIES", "3")),
                max_wait=int(os.getenv("EVAL_RAGAS_MAX_WAIT", "20")),
                max_workers=1,
            ),
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
        scores = {key: _score_value(value) for key, value in scores.items()}
        missing_scores = [
            key
            for key in [
                "faithfulness",
                "answer_relevancy",
                "context_precision",
                "context_recall",
            ]
            if scores.get(key) is None
        ]
        if len(missing_scores) == 4:
            scores["status"] = "no_scores"
        elif missing_scores:
            scores["status"] = "completed_partial"
            scores["missing_scores"] = missing_scores
        else:
            scores["status"] = "completed"
        scores["metadata"] = {
            "query_count": len(test_queries),
            "metric_jobs": len(test_queries) * 4,
            "judge_model": judge_model,
            **(metadata or {}),
        }
        SCORES_PATH.write_text(json.dumps(scores, indent=2), encoding="utf-8")
        return scores
    except Exception as exc:
        message = str(exc)
        failure = {
            "status": "rate_limited" if _is_rate_limit_error(message) else "failed",
            "reason": message,
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
            "metadata": {
                "query_count": len(test_queries),
                "metric_jobs": len(test_queries) * 4,
                **(metadata or {}),
            },
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
