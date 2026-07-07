"""Indexa o corpus BNCC no pgvector para RAG (seção 6.2 do CLAUDE.md).

Requer EMBEDDINGS_API_URL/KEY configurados e banco Postgres de pé.

Uso (a partir de backend/):
    python ../scripts/seed_bncc.py                       # amostra embutida
    python ../scripts/seed_bncc.py --file corpus.json    # corpus completo

Formato do JSON externo: lista de {"content": str, "source": str, "metadata": dict}
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

# Amostra de habilidades BNCC para validar o pipeline de RAG end-to-end.
# O corpus completo (~500 habilidades) deve ser fornecido via --file.
SAMPLE_BNCC_CHUNKS = [
    {
        "content": "EF09MA06: Compreender as funções como relações de dependência unívoca entre "
        "duas variáveis e suas representações numérica, algébrica e gráfica e utilizar esse "
        "conceito para analisar situações que envolvam relações funcionais entre duas variáveis.",
        "source": "bncc",
        "metadata": {"skill": "EF09MA06", "subject": "Matemática", "grade": "9ano_ef"},
    },
    {
        "content": "EF09MA05: Resolver e elaborar problemas que envolvam porcentagens, com a ideia "
        "de aplicação de percentuais sucessivos e a determinação das taxas percentuais, "
        "preferencialmente com o uso de tecnologias digitais, no contexto da educação financeira.",
        "source": "bncc",
        "metadata": {"skill": "EF09MA05", "subject": "Matemática", "grade": "9ano_ef"},
    },
    {
        "content": "EF09MA13: Demonstrar relações métricas do triângulo retângulo, entre elas o "
        "teorema de Pitágoras, utilizando, inclusive, a semelhança de triângulos.",
        "source": "bncc",
        "metadata": {"skill": "EF09MA13", "subject": "Matemática", "grade": "9ano_ef"},
    },
    {
        "content": "EF89LP33: Ler, de forma autônoma, e compreender — selecionando procedimentos e "
        "estratégias de leitura adequados a diferentes objetivos — romances, contos, crônicas, "
        "poemas e outros textos literários, expressando avaliação sobre o texto lido.",
        "source": "bncc",
        "metadata": {"skill": "EF89LP33", "subject": "Língua Portuguesa", "grade": "8-9ano_ef"},
    },
    {
        "content": "EF09CI14: Descrever a composição e a estrutura do Sistema Solar (Sol, planetas "
        "rochosos, planetas gigantes gasosos e corpos menores), assim como a localização do "
        "Sistema Solar na nossa Galáxia (a Via Láctea) e dela no Universo.",
        "source": "bncc",
        "metadata": {"skill": "EF09CI14", "subject": "Ciências", "grade": "9ano_ef"},
    },
]


async def seed(file_path: str | None) -> None:
    if not embeddings_enabled():
        logger.error("embeddings_not_configured", hint="Defina EMBEDDINGS_API_URL e EMBEDDINGS_API_KEY")
        return

    if file_path:
        chunks = json.loads(Path(file_path).read_text(encoding="utf-8"))
    else:
        chunks = SAMPLE_BNCC_CHUNKS
        logger.info("using_builtin_sample", count=len(chunks))

    async with async_session_maker() as db:
        await ensure_vector_extension(db)
        total = await index_chunks(db, chunks)
        logger.info("bncc_indexed", chunks=total)

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexa corpus BNCC no pgvector")
    parser.add_argument("--file", default=None, help="JSON com o corpus completo")
    args = parser.parse_args()
    asyncio.run(seed(args.file))
