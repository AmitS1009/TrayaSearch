import asyncio
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "backend"))

from app.scraper import scrape_traya_products  # noqa: E402


async def main() -> None:
    try:
        products = await scrape_traya_products()
        output_path = ROOT_DIR / "data" / "products.json"
        output_path.write_text(
            json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Scraped {len(products)} products to {output_path}.")
    except Exception as exc:
        raise RuntimeError(f"Scraper run failed: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
