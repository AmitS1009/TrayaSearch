import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas
from .auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from .config import settings
from .database import AsyncSessionLocal, get_db, init_db
from .evaluation.ragas_eval import get_saved_scores
from .scraper import scrape_and_sync
from .services import rag_service
from .services.vector_store import hybrid_retriever


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _product_dict(product: models.Product) -> dict:
    try:
        return {
            "id": product.id,
            "title": product.title,
            "price": product.price,
            "description": product.description or "",
            "features": product.features or [],
            "image_url": product.image_url,
            "category": product.category,
            "url": product.url,
        }
    except Exception as exc:
        raise RuntimeError(f"Unable to serialize product: {exc}") from exc


async def _seed_and_index_products() -> None:
    try:
        async with AsyncSessionLocal() as db:
            products = list((await db.scalars(select(models.Product))).all())
            if not products:
                data_path = Path(__file__).resolve().parents[2] / "data" / "products.json"
                raw_products = await asyncio.to_thread(
                    data_path.read_text, encoding="utf-8"
                )
                for item in json.loads(raw_products):
                    db.add(models.Product(**item))
                await db.commit()
                products = list((await db.scalars(select(models.Product))).all())
            await hybrid_retriever.sync_products([_product_dict(product) for product in products])
    except Exception as exc:
        logger.warning("Startup product indexing did not complete: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await init_db()
        await _seed_and_index_products()
        if settings.scraper_enabled:
            asyncio.create_task(scrape_and_sync())
            scheduler.add_job(
                scrape_and_sync,
                "interval",
                hours=24,
                id="product_scrape",
                replace_existing=True,
            )
            scheduler.start()
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root() -> dict:
    try:
        return {"message": "Welcome to Neusearch AI", "version": "2.0.0"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
async def health() -> dict:
    try:
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/products", response_model=list[schemas.Product])
async def read_products(
    db: Annotated[AsyncSession, Depends(get_db)], skip: int = 0, limit: int = 100
) -> list[models.Product]:
    try:
        return list((await db.scalars(select(models.Product).offset(skip).limit(limit))).all())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load products") from exc


@app.get("/products/{product_id}", response_model=schemas.Product)
async def read_product(
    product_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> models.Product:
    try:
        product = await db.get(models.Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load product") from exc


@app.post("/auth/register", response_model=schemas.TokenResponse, status_code=201)
async def register(
    payload: schemas.RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> schemas.TokenResponse:
    try:
        existing = await db.scalar(select(models.User).where(models.User.email == payload.email))
        if existing:
            raise HTTPException(status_code=409, detail="Email is already registered")
        user = models.User(
            email=payload.email.lower(), hashed_password=hash_password(payload.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return schemas.TokenResponse(access_token=create_access_token({"sub": user.id}))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to register user") from exc


@app.post("/auth/login", response_model=schemas.TokenResponse)
async def login(
    payload: schemas.LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> schemas.TokenResponse:
    try:
        user = await db.scalar(
            select(models.User).where(models.User.email == payload.email.lower())
        )
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        return schemas.TokenResponse(access_token=create_access_token({"sub": user.id}))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to log in") from exc


@app.get("/auth/me", response_model=schemas.UserResponse)
async def me(
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.User:
    try:
        return current_user
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load user") from exc


@app.post("/chat")
async def chat(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: schemas.ChatRequest | None = None,
    query: str | None = Query(default=None, max_length=2000),
) -> dict:
    try:
        user_query = payload.query if payload else query
        if not user_query or not user_query.strip():
            raise HTTPException(status_code=422, detail="Query is required")
        result = await rag_service.generate_response(user_query.strip())
        history = models.ChatHistory(
            user_id=current_user.id,
            query=user_query.strip(),
            response=result["response"],
            retrieved_docs=result["products"],
            self_rag_retries=result["retries"],
        )
        db.add(history)
        await db.commit()
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail="Unable to answer query") from exc


@app.get("/chat/history", response_model=list[schemas.ChatHistoryResponse])
async def chat_history(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[models.ChatHistory]:
    try:
        result = await db.scalars(
            select(models.ChatHistory)
            .where(models.ChatHistory.user_id == current_user.id)
            .order_by(models.ChatHistory.created_at.desc())
            .limit(100)
        )
        return list(result.all())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load chat history") from exc


@app.get("/evaluation/scores")
async def evaluation_scores(
    _: Annotated[models.User, Depends(get_current_user)]
) -> dict:
    try:
        return get_saved_scores()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load evaluation scores") from exc
