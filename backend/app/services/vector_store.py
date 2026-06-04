import asyncio
import logging
import re
from collections import defaultdict
from typing import Any

from qdrant_client import AsyncQdrantClient, models
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from ..config import settings


logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self, rrf_k: int = 60) -> None:
        api_key = settings.qdrant_api_key if settings.qdrant_url.startswith("https://") else None
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url, api_key=api_key
        )
        self.collection_name = settings.qdrant_collection
        self.rrf_k = rrf_k
        self._embedding_model: SentenceTransformer | None = None
        self._bm25: BM25Okapi | None = None
        self._documents: list[dict[str, Any]] = []

    def _model(self) -> SentenceTransformer:
        try:
            if self._embedding_model is None:
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embedding_model
        except Exception as exc:
            raise RuntimeError(f"Unable to load embedding model: {exc}") from exc

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        try:
            return re.findall(r"[a-z0-9]+", text.lower())
        except Exception:
            return []

    @staticmethod
    def product_document(product: dict[str, Any]) -> str:
        try:
            features = ", ".join(product.get("features") or [])
            return (
                f"{product.get('title', '')}. {product.get('description', '')}. "
                f"Features: {features}. Category: {product.get('category', '')}"
            ).strip()
        except Exception:
            return str(product)

    async def initialize(self) -> None:
        try:
            exists = await self.client.collection_exists(self.collection_name)
            if not exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384, distance=models.Distance.COSINE
                    ),
                )
        except Exception as exc:
            logger.warning("Qdrant is unavailable during initialization: %s", exc)

    async def sync_products(self, products: list[dict[str, Any]]) -> None:
        try:
            self._documents = [
                {**product, "text": self.product_document(product)} for product in products
            ]
            tokenized = [self._tokenize(product["text"]) for product in self._documents]
            self._bm25 = BM25Okapi(tokenized) if tokenized else None
            if not products:
                return

            await self.initialize()
            texts = [product["text"] for product in self._documents]
            vectors = await asyncio.to_thread(
                self._model().encode, texts, normalize_embeddings=True
            )
            points = [
                models.PointStruct(
                    id=int(product["id"]),
                    vector=vector.tolist(),
                    payload=product,
                )
                for product, vector in zip(self._documents, vectors, strict=True)
            ]
            await self.client.upsert(
                collection_name=self.collection_name, points=points, wait=True
            )
        except Exception as exc:
            logger.warning("Product vector sync failed; BM25 remains available: %s", exc)

    async def _dense_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            vector = await asyncio.to_thread(
                self._model().encode, query, normalize_embeddings=True
            )
            response = await self.client.query_points(
                collection_name=self.collection_name,
                query=vector.tolist(),
                limit=limit,
                with_payload=True,
            )
            return [
                {**(point.payload or {}), "dense_score": float(point.score)}
                for point in response.points
            ]
        except Exception as exc:
            logger.warning("Dense retrieval failed: %s", exc)
            return []

    async def _sparse_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            if not self._bm25 or not self._documents:
                return []
            scores = self._bm25.get_scores(self._tokenize(query))
            ranked = sorted(
                zip(self._documents, scores, strict=True),
                key=lambda item: float(item[1]),
                reverse=True,
            )[:limit]
            return [
                {**document, "sparse_score": float(score)}
                for document, score in ranked
                if score > 0
            ]
        except Exception as exc:
            logger.warning("Sparse retrieval failed: %s", exc)
            return []

    async def retrieve(self, query: str, top_k: int = 20) -> list[dict[str, Any]]:
        try:
            dense, sparse = await asyncio.gather(
                self._dense_search(query, top_k), self._sparse_search(query, top_k)
            )
            fused_scores: defaultdict[str, float] = defaultdict(float)
            documents: dict[str, dict[str, Any]] = {}
            for results in (dense, sparse):
                for rank, document in enumerate(results, start=1):
                    product_id = str(document["id"])
                    fused_scores[product_id] += 1 / (self.rrf_k + rank)
                    documents[product_id] = {**documents.get(product_id, {}), **document}

            ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
            return [
                {**documents[product_id], "rrf_score": fused_scores[product_id]}
                for product_id in ranked_ids[:top_k]
            ]
        except Exception as exc:
            logger.exception("Hybrid retrieval failed")
            raise RuntimeError(f"Hybrid retrieval failed: {exc}") from exc


hybrid_retriever = HybridRetriever()


async def add_products_to_vector_db(products: list[dict[str, Any]]) -> None:
    try:
        await hybrid_retriever.sync_products(products)
    except Exception as exc:
        raise RuntimeError(f"Unable to index products: {exc}") from exc


async def query_products(query_text: str, n_results: int = 5) -> list[dict[str, Any]]:
    try:
        return await hybrid_retriever.retrieve(query_text, top_k=n_results)
    except Exception as exc:
        raise RuntimeError(f"Unable to query products: {exc}") from exc
