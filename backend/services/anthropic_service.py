"""Wrapper único do provedor de IA.

NUNCA instanciar o client Anthropic diretamente em outros arquivos (seção 3.2 do
CLAUDE.md). Usa AsyncAnthropic para não bloquear o event loop do FastAPI.

O provedor é configurável via env (ANTHROPIC_BASE_URL + AI_MODEL): qualquer API
compatível com a Messages API da Anthropic funciona sem mudar nenhum agente.
"""

import json
from collections.abc import AsyncGenerator

import anthropic
import structlog

from core.config import settings

logger = structlog.get_logger()

client = anthropic.AsyncAnthropic(
    api_key=settings.anthropic_api_key or None,
    base_url=settings.anthropic_base_url or None,
)

FABLE_5_MODEL = settings.ai_model


async def stream_tutor_response(
    system_prompt: str,
    messages: list[dict],
    student_id: str,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """Stream de resposta do modelo para a sessão de tutoria."""
    try:
        async with client.messages.stream(
            model=FABLE_5_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError as e:
        logger.error("anthropic_api_error", student_id=student_id, error=str(e))
        raise


async def complete_json(
    system_prompt: str,
    user_prompt: str,
    student_id: str,
    max_tokens: int = 2048,
) -> dict:
    """Chamada não-streaming que retorna JSON parseado.

    Usa prefill de "{" para forçar saída JSON pura, sem prosa ao redor.
    """
    try:
        response = await client.messages.create(
            model=FABLE_5_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": "{"},
            ],
        )
    except anthropic.APIError as e:
        logger.error("anthropic_api_error", student_id=student_id, error=str(e))
        raise

    raw = "{" + response.content[0].text
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("anthropic_invalid_json", student_id=student_id, error=str(e))
        raise ValueError("O modelo retornou JSON inválido") from e


async def analyze_image(
    image_base64: str,
    mime_type: str,
    prompt: str,
    student_id: str,
    max_tokens: int = 2048,
) -> str:
    """Análise multimodal de imagem (vision) — usada pelo vision_agent."""
    try:
        response = await client.messages.create(
            model=FABLE_5_MODEL,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
    except anthropic.APIError as e:
        logger.error("anthropic_vision_error", student_id=student_id, error=str(e))
        raise
    return response.content[0].text
