"""RAG sobre o corpus BNCC/ENEM indexado em pgvector (seção 6.2 do CLAUDE.md).

Antes de cada resposta do tutor sobre um tópico, busca semântica no corpus para
grounding factual. Degrada graciosamente: sem embeddings configurados ou sem
pgvector (ex.: testes em SQLite), retorna contexto vazio.
"""

import uuid

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import KnowledgeChunk
from services.embedding_service import embed_query, embeddings_enabled

logger = structlog.get_logger()


async def search_knowledge(
    db: AsyncSession,
    query: str,
    subject_id: uuid.UUID | None = None,
    limit: int = 4,
) -> list[KnowledgeChunk]:
    """Busca semântica por similaridade de cosseno no pgvector."""
    if not embeddings_enabled():
        return []
    try:
        query_embedding = await embed_query(query)
        stmt = select(KnowledgeChunk).order_by(
            KnowledgeChunk.embedding.cosine_distance(query_embedding)
        )
        if subject_id is not None:
            stmt = stmt.where(KnowledgeChunk.subject_id == subject_id)
        result = await db.scalars(stmt.limit(limit))
        return list(result)
    except Exception as e:
        logger.warning("rag_search_failed", error=str(e))
        return []


async def build_grounding_context(
    db: AsyncSession,
    query: str,
    subject_id: uuid.UUID | None = None,
) -> str:
    """Formata os chunks recuperados para injeção no system prompt do tutor."""
    chunks = await search_knowledge(db, query, subject_id)
    if not chunks:
        return ""
    lines = [f"[{c.source or 'referência'}] {c.content}" for c in chunks]
    return "CONHECIMENTO DE REFERÊNCIA (currículo oficial — use para fundamentar a explicação):\n" + "\n".join(lines)


async def index_chunks(
    db: AsyncSession,
    chunks: list[dict],
) -> int:
    """Indexa chunks no pgvector. Cada dict: {content, source, subject_id?, topic_id?, metadata?}.

    Usado pelos scripts seed_bncc.py e seed_enem.py.
    """
    from services.embedding_service import embed_texts

    embeddings = await embed_texts([c["content"] for c in chunks])
    for chunk_data, embedding in zip(chunks, embeddings):
        db.add(
            KnowledgeChunk(
                content=chunk_data["content"],
                source=chunk_data.get("source"),
                subject_id=chunk_data.get("subject_id"),
                topic_id=chunk_data.get("topic_id"),
                embedding=embedding,
                meta=chunk_data.get("metadata", {}),
            )
        )
    await db.commit()
    return len(chunks)


async def ensure_vector_extension(db: AsyncSession) -> None:
    """Garante a extensão pgvector antes de criar a tabela (apenas Postgres)."""
    await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await db.commit()
