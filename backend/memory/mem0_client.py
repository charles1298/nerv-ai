"""Integração Mem0 por aluno (seção 3.3 do CLAUDE.md).

Toda memória de aluno usa o student_id como user_id no Mem0.
Sem MEM0_API_KEY configurada, as funções degradam graciosamente (tutoria
funciona sem memória de longo prazo) — nunca derrubam uma sessão.
"""

import asyncio

import structlog

from core.config import settings

logger = structlog.get_logger()

_mem0_client = None


def _get_client():
    """Client Mem0 lazy — None quando não configurado ou indisponível."""
    global _mem0_client
    if not settings.mem0_api_key:
        return None
    if _mem0_client is None:
        try:
            from mem0 import MemoryClient

            _mem0_client = MemoryClient(api_key=settings.mem0_api_key)
        except Exception as e:
            logger.warning("mem0_init_failed", error=str(e))
            return None
    return _mem0_client


async def get_student_context(student_id: str, query: str) -> str:
    """Recupera memórias relevantes do aluno para enriquecer o system prompt."""
    client = _get_client()
    if client is None:
        return "Primeira interação com este aluno. Sem histórico."
    try:
        # SDK do Mem0 é síncrono — roda em thread para não bloquear o loop
        memories = await asyncio.to_thread(
            client.search, query=query, user_id=student_id, limit=10
        )
    except Exception as e:
        logger.warning("mem0_search_failed", student_id=student_id, error=str(e))
        return "Histórico temporariamente indisponível."

    if not memories:
        return "Primeira interação com este aluno. Sem histórico."

    context_lines = [f"- {m['memory']}" for m in memories]
    return "Contexto do aluno (memórias anteriores):\n" + "\n".join(context_lines)


async def save_session_insights(student_id: str, insights: list[str]) -> None:
    """Salva insights da sessão — dificuldades, avanços, conceitos aprendidos."""
    client = _get_client()
    if client is None:
        logger.info("mem0_disabled_insights_skipped", student_id=student_id, count=len(insights))
        return
    for insight in insights:
        try:
            await asyncio.to_thread(
                client.add,
                messages=[{"role": "user", "content": insight}],
                user_id=student_id,
            )
        except Exception as e:
            logger.warning("mem0_add_failed", student_id=student_id, error=str(e))
