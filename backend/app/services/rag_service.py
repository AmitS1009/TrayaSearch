from typing import Any

from ..llm import llm
from ..reranker import reranker
from ..self_rag import SelfRAGPipeline
from .vector_store import hybrid_retriever


pipeline = SelfRAGPipeline(llm=llm, retriever=hybrid_retriever, reranker=reranker)


async def generate_response(query: str) -> dict[str, Any]:
    try:
        result = await pipeline.run(query)
        return {
            "response": result["answer"],
            "products": result.get("retrieved_docs", []),
            "retries": result.get("retries", 0),
            "warning": result.get("warning"),
            "self_rag_trace": result.get("self_rag_trace", []),
        }
    except Exception as exc:
        raise RuntimeError(f"Unable to generate response: {exc}") from exc
