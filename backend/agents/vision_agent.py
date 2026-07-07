"""Agente de visão — análise de fotos de provas, cadernos e exercícios (seção 5.4)."""

import structlog

from services.anthropic_service import analyze_image

logger = structlog.get_logger()

VISION_PROMPT_TEMPLATE = """Contexto do aluno: {student_context}

Pergunta do aluno: {student_prompt}

Analise esta imagem educacional. Identifique:
1. Tipo de conteúdo (exercício, prova, gráfico, diagrama, texto...)
2. Matéria e tópico
3. Responda à pergunta do aluno de forma didática
4. Se houver erros do aluno visíveis, explique com cuidado
5. Se for um exercício não resolvido, guie passo a passo (sem dar a resposta direta)

Use notação LaTeX inline ($...$) para expressões matemáticas."""


async def analyze_uploaded_image(
    image_base64: str,
    mime_type: str,
    student_prompt: str,
    student_context: str,
    student_id: str,
) -> dict:
    """Analisa imagem enviada pelo aluno via vision do modelo.

    student_prompt: o que o aluno quer saber sobre a imagem.
    """
    prompt = VISION_PROMPT_TEMPLATE.format(
        student_context=student_context,
        student_prompt=student_prompt or "Analise e me ajude a entender este conteúdo.",
    )
    analysis = await analyze_image(
        image_base64=image_base64,
        mime_type=mime_type,
        prompt=prompt,
        student_id=student_id,
    )
    return {"analysis": analysis}
