"""Agente principal de tutoria (seção 5.1 do CLAUDE.md).

Fase 2: contexto vem do Mem0 (memória de longo prazo por aluno) + grounding
factual via RAG no corpus BNCC. Ambos degradam graciosamente quando não
configurados — a tutoria nunca para por causa deles.
"""

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from memory.bncc_rag import build_grounding_context
from memory.mem0_client import get_student_context
from models import SessionMessage, TutoringSession, User
from services.anthropic_service import complete_json, stream_tutor_response

logger = structlog.get_logger()

TUTOR_SYSTEM_PROMPT = """Você é NERV, tutor de IA educacional para estudantes brasileiros do Ensino Fundamental e Médio.
Você tem acesso ao histórico completo deste aluno e deve usá-lo para personalizar cada resposta.
Você é paciente, encorajador e nunca dá a resposta diretamente — você guia o aluno a descobrir.
Quando o aluno errar, elogie o esforço, identifique o erro com clareza e reformule a explicação.
Você conhece profundamente a BNCC e alinha cada explicação às competências e habilidades exigidas.
Mantenha um equilíbrio entre rigor acadêmico e linguagem acessível para a faixa etária do aluno.
Use exemplos brasileiros sempre que possível.
Para matemática, use notação LaTeX inline ($...$) para todas as expressões.
Para ciências, cite experimentos simples que o aluno pode fazer em casa.
Para português, pratique redação com temas reais do ENEM recente.

CONTEXTO DO ALUNO:
{student_context}

{grounding}

PERFIL:
Nome: {student_name}
Série: {grade}
Matéria: {subject}
Tópico desta sessão: {topic}"""

INSIGHTS_SYSTEM_PROMPT = """Você é o analisador pedagógico do NERV AI. Dada a transcrição de uma sessão de tutoria,
extraia insights para a memória de longo prazo do aluno e avalie a qualidade da sessão.

Responda APENAS com JSON neste formato:
{
  "insights": [
    "Tópicos dominados nesta sessão: ...",
    "Dificuldades identificadas: ...",
    "Estilo de aprendizagem observado: visual | auditivo | prático | leitura",
    "Próximos tópicos recomendados: ..."
  ],
  "quality_score": 0.85
}
quality_score entre 0.0 e 1.0 reflete engajamento e progresso pedagógico da sessão.
Cada insight deve ser uma frase autocontida e específica sobre ESTE aluno."""


def build_system_prompt(
    student: User,
    session: TutoringSession,
    student_context: str = "Primeira interação com este aluno. Sem histórico.",
    grounding: str = "",
) -> str:
    return TUTOR_SYSTEM_PROMPT.format(
        student_context=student_context,
        grounding=grounding,
        student_name=student.name,
        grade=student.grade or "não informada",
        subject=session.subject.name if session.subject else "geral",
        topic=session.topic.name if session.topic else "livre",
    )


def build_message_history(history: list[SessionMessage], new_user_message: str) -> list[dict]:
    """Converte mensagens persistidas + a nova mensagem para o formato da Claude API."""
    messages: list[dict] = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": new_user_message})
    return messages


async def run_tutor_turn(
    student: User,
    session: TutoringSession,
    history: list[SessionMessage],
    user_message: str,
    db: AsyncSession | None = None,
) -> AsyncGenerator[str, None]:
    """Executa um turno de tutoria, retornando o stream de texto do modelo."""
    student_context = await get_student_context(str(student.id), user_message)
    grounding = ""
    if db is not None:
        grounding = await build_grounding_context(db, user_message, session.subject_id)

    system_prompt = build_system_prompt(student, session, student_context, grounding)
    messages = build_message_history(history, user_message)
    async for chunk in stream_tutor_response(
        system_prompt=system_prompt,
        messages=messages,
        student_id=str(student.id),
    ):
        yield chunk


async def generate_session_insights(
    student: User,
    messages: list[SessionMessage],
) -> tuple[list[str], float | None]:
    """Extrai insights pedagógicos da sessão para o Mem0 (chamado em /end).

    Falhas retornam vazio — encerrar a sessão nunca depende do modelo.
    """
    if not messages:
        return [], None

    transcript = "\n".join(f"{m.role}: {m.content}" for m in messages[-40:])
    try:
        raw = await complete_json(
            system_prompt=INSIGHTS_SYSTEM_PROMPT,
            user_prompt=f"Transcrição da sessão:\n\n{transcript}",
            student_id=str(student.id),
        )
        insights = [str(i) for i in raw.get("insights", [])]
        quality = raw.get("quality_score")
        quality_score = float(quality) if quality is not None else None
        return insights, quality_score
    except Exception as e:
        logger.warning("insights_generation_failed", student_id=str(student.id), error=str(e))
        return [], None
