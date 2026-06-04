import json
import logging
import re
from typing import Any

from groq import AsyncGroq

from .config import settings


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Neusearch AI, an expert e-commerce product advisor.
You help users find the right products based on their needs and concerns.
Rules:
- Only recommend products present in the provided context
- Explain why each product matches the user's concern
- If no relevant products are found, say so honestly
- Be conversational, empathetic, and concise
- Never hallucinate product names, prices, or features"""


class GroqLLM:
    def __init__(self) -> None:
        self.client = AsyncGroq(api_key=settings.groq_api_key) if settings.groq_api_key else None

    @staticmethod
    def _context_text(context: list[dict[str, Any]] | None) -> str:
        try:
            if not context:
                return "No product context was provided."
            return "\n\n".join(
                (
                    f"Product: {product.get('title')}\n"
                    f"Price: {product.get('price')}\n"
                    f"Description: {product.get('description') or ''}\n"
                    f"Features: {', '.join(product.get('features') or [])}\n"
                    f"URL: {product.get('url')}"
                )
                for product in context
            )
        except Exception:
            return "Product context could not be formatted."

    async def _complete(
        self, messages: list[dict[str, str]], temperature: float = 0.1, max_tokens: int = 500
    ) -> str:
        try:
            if not self.client:
                raise RuntimeError("GROQ_API_KEY is not configured")
            response = await self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("Groq completion unavailable: %s", exc)
            raise

    async def generate(
        self, query: str, context: list[dict[str, Any]] | None = None
    ) -> str:
        try:
            return await self._complete(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"User concern: {query}\n\nAvailable products:\n"
                            f"{self._context_text(context)}"
                        ),
                    },
                ],
                temperature=0.3,
            )
        except Exception:
            if not context:
                return "Hi! Tell me what product or concern you would like help with."
            recommendations = [
                f"- **{product.get('title')}** ({product.get('price')}): "
                f"{product.get('description') or product.get('text', '')[:180]}"
                for product in context[:5]
            ]
            return "Here are the closest matches I found:\n\n" + "\n\n".join(recommendations)

    async def generate_json(self, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            content = await self._complete(
                [
                    {
                        "role": "system",
                        "content": "Return only valid JSON matching the requested schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=250,
            )
            match = re.search(r"\{.*\}", content, re.DOTALL)
            return json.loads(match.group(0) if match else content)
        except Exception:
            return fallback

    async def rewrite_query(self, query: str, attempt: int) -> str:
        try:
            response = await self._complete(
                [
                    {
                        "role": "user",
                        "content": (
                            "Rewrite this e-commerce product search query to improve retrieval. "
                            f"Return only the rewritten query. Attempt {attempt + 1}: {query}"
                        ),
                    }
                ],
                max_tokens=80,
            )
            return response.strip() or query
        except Exception:
            return f"{query} benefits ingredients concern treatment"


llm = GroqLLM()
