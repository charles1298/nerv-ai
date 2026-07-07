"""Indexa banco de questões ENEM no pgvector para RAG (seção 6.2 do CLAUDE.md).

As provas do ENEM são domínio público (INEP). Este script espera um JSON com as
questões já extraídas — a extração dos PDFs oficiais fica fora do repositório.

Uso (a partir de backend/):
    python ../scripts/seed_enem.py --file questoes_enem.json

Formato: lista de {"year": int, "question": str, "subject": str, "answer": str}
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import structlog

from core.database import async_session_maker, engine
from memory.bncc_rag import ensure_vector_extension, index_chunks
from services.embedding_service import embeddings_enabled

logger = structlog.get_logger()

BATCH_SIZE = 50


async def seed(file_path: str) -> None:
    if not embeddings_enabled():
        logger.error("embeddings_not_configured", hint="Defina EMBEDDINGS_API_URL e EMBEDDINGS_API_KEY")
        return

    questions = json.loads(Path(file_path).read_text(encoding="utf-8"))
    chunks = [
        {
            "content": f"Questão ENEM {q['year']} ({q.get('subject', 'geral')}): {q['question']} "
            f"Gabarito: {q.get('answer', 'não informado')}",
            "source": "enem",
            "metadata": {"year": q["year"], "subject": q.get("subject")},
        }
        for q in questions
    ]

    async with async_session_maker() as db:
        await ensure_vector_extension(db)
        total = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            total += await index_chunks(db, chunks[i : i + BATCH_SIZE])
            logger.info("enem_batch_indexed", progress=f"{total}/{len(chunks)}")

    await engine.dispose()
    logger.info("enem_indexed", chunks=total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexa questões ENEM no pgvector")
    parser.add_argument("--file", required=True, help="JSON com as questões")
    args = parser.parse_args()
    asyncio.run(seed(args.file))
