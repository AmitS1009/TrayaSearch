import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app import models
from app.database import AsyncSessionLocal, init_db


async def ingest_data() -> None:
    try:
        await init_db()
        data_path = Path(__file__).resolve().parent.parent / "data" / "products.json"
        products = json.loads(data_path.read_text(encoding="utf-8"))
        async with AsyncSessionLocal() as db:
            count = 0
            for item in products:
                existing = await db.scalar(
                    select(models.Product).where(models.Product.url == item["url"])
                )
                if not existing:
                    db.add(models.Product(**item))
                    count += 1
            await db.commit()
        print(f"Ingested {count} new products.")
    except Exception as exc:
        raise RuntimeError(f"Unable to ingest product data: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(ingest_data())
