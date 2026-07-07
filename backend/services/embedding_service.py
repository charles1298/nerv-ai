"""Embeddings para o RAG — endpoint plugável compatível com OpenAI /v1/embeddings.

Configurado via EMBEDDINGS_API_URL / EMBEDDINGS_API_KEY / EMBEDDINGS_MODEL.
Sem configuração, o RAG fica desativado (busca retorna vazio) sem quebrar o tutor.
"""

import httpx
import structlog

from core.config import settings

logger = structlog.get_logger()


def embeddings_enabled() -> bool:
    return bool(settings.embeddings_api_url and settings.embeddings_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Gera embeddings para uma lista de textos. Levanta RuntimeError se desativado."""
    if not embeddings_enabled():
        raise RuntimeError("Embeddings não configurados (EMBEDDINGS_API_URL/KEY)")

    async with httpx.AsyncClient(timeout=60) as http:
        resp = await http.post(
            f"{settings.embeddings_api_url.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {settings.embeddings_api_key}"},
            json={"model": settings.embeddings_model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()

    # Formato OpenAI: {"data": [{"index": 0, "embedding": [...]}, ...]}
    items = sorted(data["data"], key=lambda d: d["index"])
    return [item["embedding"] for item in items]


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]
