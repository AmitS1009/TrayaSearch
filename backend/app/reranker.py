import asyncio
import logging
from typing import Any

from sentence_transformers import CrossEncoder


logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    def __init__(self) -> None:
        self._model: CrossEncoder | None = None

    def _load_model(self) -> CrossEncoder:
        try:
            if self._model is None:
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            return self._model
        except Exception as exc:
            raise RuntimeError(f"Unable to load reranker: {exc}") from exc

    async def rerank(
        self, query: str, documents: list[dict[str, Any]], top_k: int = 5
    ) -> list[dict[str, Any]]:
        try:
            if not documents:
                return []
            pairs = [(query, document.get("text", "")) for document in documents]
            scores = await asyncio.to_thread(self._load_model().predict, pairs)
            ranked = sorted(
                (
                    {**document, "reranker_score": float(score)}
                    for document, score in zip(documents, scores, strict=True)
                ),
                key=lambda document: document["reranker_score"],
                reverse=True,
            )
            return ranked[:top_k]
        except Exception as exc:
            logger.warning("Cross-encoder reranking failed; using RRF order: %s", exc)
            return documents[:top_k]


reranker = CrossEncoderReranker()
