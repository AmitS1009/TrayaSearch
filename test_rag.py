import asyncio
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.services.vector_store import hybrid_retriever  # noqa: E402


async def main() -> None:
    try:
        results = await hybrid_retriever.retrieve("dandruff", top_k=5)
        print(f"Retrieved {len(results)} products.")
        for product in results:
            print(product.get("title"), product.get("rrf_score"))
    except Exception as exc:
        raise RuntimeError(f"Retrieval smoke test failed: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
