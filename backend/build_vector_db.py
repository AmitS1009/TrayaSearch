import asyncio

from sqlalchemy import select

from app import models
from app.database import AsyncSessionLocal
from app.services.vector_store import hybrid_retriever


async def build_vector_index() -> None:
    try:
        async with AsyncSessionLocal() as db:
            products = list((await db.scalars(select(models.Product))).all())
            await hybrid_retriever.sync_products(
                [
                    {
                        "id": product.id,
                        "title": product.title,
                        "description": product.description or "",
                        "features": product.features or [],
                        "price": product.price,
                        "category": product.category,
                        "url": product.url,
                        "image_url": product.image_url,
                    }
                    for product in products
                ]
            )
            print(f"Indexed {len(products)} products.")
    except Exception as exc:
        raise RuntimeError(f"Unable to build vector index: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(build_vector_index())
