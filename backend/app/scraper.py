import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from . import models
from .database import AsyncSessionLocal
from .services.vector_store import hybrid_retriever


logger = logging.getLogger(__name__)
BASE_URL = "https://traya.health"
COLLECTION_URL = f"{BASE_URL}/collections/all-products"
HEADERS = {"User-Agent": "NeusearchAI/1.0 (+product-indexing)"}


async def _fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except Exception as exc:
        logger.warning("Unable to fetch %s: %s", url, exc)
        return ""


def _parse_product(html: str, url: str) -> dict[str, Any] | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.select_one("h1.product__title, .product-single__title, h1")
        if not title_tag:
            return None
        price_tag = soup.select_one(
            ".price-item--regular .money, .price__regular .price-item--regular, "
            ".product-single__price .money, .price .money"
        )
        description_tag = soup.select_one(
            ".product__description, .product-single__description"
        )
        image_tag = soup.select_one(
            ".product__media-wrapper img, .product-single__photo img, .product-image-main img"
        )
        feature_tags = soup.select(
            ".product-usp-item p, .product-usp-item span, .product-features li, "
            ".product__description li"
        )
        image_url = ""
        if image_tag:
            image_url = image_tag.get("src") or image_tag.get("data-src") or ""
            if image_url.startswith("//"):
                image_url = f"https:{image_url}"
        return {
            "title": title_tag.get_text(" ", strip=True),
            "price": price_tag.get_text(" ", strip=True) if price_tag else "Price unavailable",
            "description": (
                description_tag.get_text(" ", strip=True) if description_tag else ""
            ),
            "features": list(
                dict.fromkeys(
                    tag.get_text(" ", strip=True)
                    for tag in feature_tags
                    if tag.get_text(" ", strip=True)
                )
            )[:12],
            "image_url": image_url,
            "category": "Hair care",
            "url": url,
        }
    except Exception as exc:
        logger.warning("Unable to parse product %s: %s", url, exc)
        return None


async def scrape_traya_products(limit: int = 30) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=20, follow_redirects=True
        ) as client:
            collection_html = await _fetch(client, COLLECTION_URL)
            if not collection_html:
                return []
            soup = BeautifulSoup(collection_html, "html.parser")
            links = list(
                dict.fromkeys(
                    urljoin(BASE_URL, anchor["href"])
                    for anchor in soup.select("a[href*='/products/']")
                    if "collections" not in anchor["href"]
                )
            )[:limit]
            pages = await asyncio.gather(*(_fetch(client, link) for link in links))
            products = [
                product
                for product in (
                    _parse_product(html, link) for html, link in zip(pages, links, strict=True)
                )
                if product
            ]
            return products
    except Exception as exc:
        logger.exception("Product scrape failed")
        raise RuntimeError(f"Product scrape failed: {exc}") from exc


async def scrape_and_sync() -> int:
    try:
        scraped = await scrape_traya_products()
        if not scraped:
            return 0
        async with AsyncSessionLocal() as db:
            for item in scraped:
                existing = await db.scalar(
                    select(models.Product).where(models.Product.url == item["url"])
                )
                if existing:
                    for field, value in item.items():
                        setattr(existing, field, value)
                else:
                    db.add(models.Product(**item))
            await db.commit()
            products = (await db.scalars(select(models.Product))).all()
            await hybrid_retriever.sync_products(
                [
                    {
                        "id": product.id,
                        "title": product.title,
                        "price": product.price,
                        "description": product.description or "",
                        "features": product.features or [],
                        "image_url": product.image_url,
                        "category": product.category,
                        "url": product.url,
                    }
                    for product in products
                ]
            )
        return len(scraped)
    except Exception as exc:
        logger.exception("Scrape and sync failed")
        raise RuntimeError(f"Scrape and sync failed: {exc}") from exc
