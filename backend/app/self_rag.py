from enum import Enum
from typing import Any

from langsmith import traceable


class RetrievalDecision(Enum):
    RETRIEVE = "retrieve"
    SKIP = "skip"


class RelevanceScore(Enum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"


class GroundednessScore(Enum):
    GROUNDED = "grounded"
    NOT_GROUNDED = "not_grounded"


class SelfRAGPipeline:
    def __init__(self, llm: Any, retriever: Any, reranker: Any) -> None:
        self.llm = llm
        self.retriever = retriever
        self.reranker = reranker
        self.max_retries = 2

    @traceable(name="self_rag_pipeline")
    async def run(self, query: str) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        best_answer = ""
        best_docs: list[dict[str, Any]] = []
        try:
            retrieval_decision = await self.decide_retrieval(query)
            trace.append({"step": "retrieval_decision", "result": retrieval_decision.value})
            if retrieval_decision == RetrievalDecision.SKIP:
                response = await self.llm.generate(query, context=None)
                return {
                    "answer": response,
                    "retrieved_docs": [],
                    "retries": 0,
                    "self_rag_trace": trace,
                }

            current_query = query
            for retry_count in range(self.max_retries + 1):
                docs = await self.retrieve(current_query)
                reranked_docs = await self.reranker.rerank(current_query, docs, top_k=5)
                trace.append(
                    {
                        "step": "retrieve_and_rerank",
                        "query": current_query,
                        "retrieved": len(docs),
                        "reranked": len(reranked_docs),
                    }
                )

                relevance_results = [
                    await self.check_relevance(current_query, doc) for doc in reranked_docs
                ]
                relevant_docs = [
                    doc
                    for doc, result in zip(reranked_docs, relevance_results, strict=True)
                    if result == RelevanceScore.RELEVANT
                ]
                trace.append({"step": "relevance_check", "relevant": len(relevant_docs)})
                if not relevant_docs:
                    current_query = await self.rewrite_query(query, retry_count)
                    trace.append({"step": "query_rewrite", "query": current_query})
                    continue

                best_docs = relevant_docs
                best_answer = await self.llm.generate(query, context=relevant_docs)
                groundedness = await self.check_groundedness(best_answer, relevant_docs)
                trace.append({"step": "groundedness_check", "result": groundedness.value})
                if groundedness == GroundednessScore.GROUNDED:
                    return {
                        "answer": best_answer,
                        "retrieved_docs": relevant_docs,
                        "retries": retry_count,
                        "self_rag_trace": trace,
                    }
                current_query = await self.rewrite_query(query, retry_count)
                trace.append({"step": "query_rewrite", "query": current_query})

            if not best_answer:
                best_answer = (
                    "I could not find enough relevant product information to answer "
                    "confidently. Please try describing the concern differently."
                )
            return {
                "answer": best_answer,
                "retrieved_docs": best_docs,
                "retries": self.max_retries,
                "warning": "Low confidence answer",
                "self_rag_trace": trace,
            }
        except Exception as exc:
            raise RuntimeError(f"Self-RAG pipeline failed: {exc}") from exc

    async def decide_retrieval(self, query: str) -> RetrievalDecision:
        try:
            normalized = query.strip().lower()
            fallback = {
                "retrieve": normalized
                not in {"hi", "hello", "hey", "thanks", "thank you", "goodbye", "bye"}
            }
            result = await self.llm.generate_json(
                "Does this query require product information to answer? "
                f"Query: {query}\nRespond with JSON: {{\"retrieve\": true/false}}",
                fallback,
            )
            return RetrievalDecision.RETRIEVE if result.get("retrieve") else RetrievalDecision.SKIP
        except Exception:
            return RetrievalDecision.RETRIEVE

    @traceable(name="retrieval")
    async def retrieve(self, query: str) -> list[dict[str, Any]]:
        try:
            return await self.retriever.retrieve(query, top_k=20)
        except Exception as exc:
            raise RuntimeError(f"Retrieval failed: {exc}") from exc

    async def check_relevance(self, query: str, doc: dict[str, Any]) -> RelevanceScore:
        try:
            fallback = {"relevant": float(doc.get("reranker_score", 0)) > -5}
            result = await self.llm.generate_json(
                f"Is this document relevant to answering: {query}?\n"
                f"Document: {doc.get('text')}\n"
                'Respond with JSON: {"relevant": true/false}',
                fallback,
            )
            return RelevanceScore.RELEVANT if result.get("relevant") else RelevanceScore.IRRELEVANT
        except Exception:
            return RelevanceScore.IRRELEVANT

    @traceable(name="groundedness_check")
    async def check_groundedness(
        self, answer: str, docs: list[dict[str, Any]]
    ) -> GroundednessScore:
        try:
            result = await self.llm.generate_json(
                "Is this answer fully supported by the provided documents?\n"
                f"Answer: {answer}\nDocuments: {docs}\n"
                'Respond with JSON: {"grounded": true/false, "issues": []}',
                {"grounded": True, "issues": []},
            )
            return (
                GroundednessScore.GROUNDED
                if result.get("grounded")
                else GroundednessScore.NOT_GROUNDED
            )
        except Exception:
            return GroundednessScore.NOT_GROUNDED

    async def rewrite_query(self, original_query: str, attempt: int) -> str:
        try:
            return await self.llm.rewrite_query(original_query, attempt)
        except Exception:
            return original_query
