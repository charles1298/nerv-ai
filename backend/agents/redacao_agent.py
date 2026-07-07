"""Agente de avaliação de redações no modelo ENEM (seção 5.3 do CLAUDE.md)."""

import structlog

from models import User
from schemas.redacao import RedacaoAvaliacao
from services.anthropic_service import complete_json

logger = structlog.get_logger()

REDACAO_SYSTEM_PROMPT = """Você é um corretor oficial de redações do ENEM, treinado na matriz de referência do INEP.
Avalie a redação nos 5 critérios, cada um de 0 a 200 em múltiplos de 40 (níveis 0-5 do ENEM):

- C1 — Domínio da norma culta: gramática, ortografia, pontuação, concordância.
- C2 — Compreensão do tema: adequação ao tema proposto, repertório sociocultural.
- C3 — Argumentação: progressão argumentativa, coerência, coesão.
- C4 — Mecanismos linguísticos: conectivos, coesão referencial, progressão textual.
- C5 — Proposta de intervenção: proposta concreta, agentes, ações, finalidade.

Seja rigoroso e fiel aos critérios reais do ENEM. Identifique erros gramaticais com o trecho exato.
A reescrita sugerida deve melhorar um trecho fraco mantendo a voz do aluno.

Responda APENAS com JSON neste formato:
{
  "nota_total": 760,
  "notas_por_criterio": {"C1": 160, "C2": 200, "C3": 160, "C4": 160, "C5": 80},
  "analise_detalhada": {
    "pontos_fortes": ["..."],
    "pontos_fracos": ["..."],
    "erros_gramaticais": [{"trecho": "...", "erro": "...", "correcao": "..."}]
  },
  "reescrita_sugerida": "Trecho reescrito com melhorias...",
  "nota_estimada_real_enem": "Entre 640 e 720",
  "proximos_passos": ["Praticar proposta de intervenção", "Revisar conectivos adversativos"]
}
nota_total deve ser a soma exata dos 5 critérios."""


async def evaluate_essay(student: User, theme: str, content: str) -> RedacaoAvaliacao:
    """Avalia a redação completa e retorna o resultado validado."""
    user_prompt = (
        f"Série do aluno: {student.grade or 'não informada'}\n\n"
        f"TEMA PROPOSTO:\n{theme}\n\n"
        f"REDAÇÃO DO ALUNO:\n{content}"
    )
    raw = await complete_json(
        system_prompt=REDACAO_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        student_id=str(student.id),
        max_tokens=4096,
    )

    # Garante consistência aritmética mesmo se o modelo errar a soma
    if "notas_por_criterio" in raw:
        raw["nota_total"] = sum(raw["notas_por_criterio"].values())

    avaliacao = RedacaoAvaliacao.model_validate(raw)
    logger.info(
        "essay_evaluated",
        student_id=str(student.id),
        nota_total=avaliacao.nota_total,
    )
    return avaliacao
