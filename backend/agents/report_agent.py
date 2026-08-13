"""Agente de relatórios pedagógicos (seção 5.5 do CLAUDE.md).

Gera narrativas pedagógicas a partir de agregados do banco. Os dados numéricos
vêm sempre do banco (fonte da verdade) — o modelo só interpreta e recomenda.
"""

import structlog

from services.ai_service import complete_json

logger = structlog.get_logger()

REPORT_SYSTEM_PROMPT = """Você é o analista pedagógico do NERV AI. A partir dos dados quantitativos de um aluno,
produza um relatório pedagógico claro para professores, em português brasileiro.

Responda APENAS com JSON neste formato:
{
  "resumo": "Visão geral do desempenho em 2-3 frases.",
  "evolucao": "Análise da trajetória recente.",
  "pontos_fortes": ["..."],
  "pontos_atencao": ["..."],
  "recomendacoes": ["Ação concreta que o professor pode tomar", "..."],
  "proximos_topicos": ["Tópico sugerido para as próximas sessões", "..."]
}
Seja específico e acionável — evite generalidades. Baseie-se apenas nos dados fornecidos."""


async def generate_student_report(student_name: str, grade: str | None, aggregates: dict) -> dict:
    """Gera relatório individual do aluno a partir dos agregados calculados."""
    user_prompt = (
        f"Aluno: {student_name} (série: {grade or 'não informada'})\n\n"
        f"Dados de desempenho:\n{aggregates}"
    )
    report = await complete_json(
        system_prompt=REPORT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        student_id="report",
        max_tokens=2048,
    )
    logger.info("student_report_generated", student=student_name)
    return report
