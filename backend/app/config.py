import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings:
    app_name = "Neusearch AI"
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./neusearch.db")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "products")
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    scraper_enabled = os.getenv("SCRAPER_ENABLED", "false").lower() == "true"
    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
