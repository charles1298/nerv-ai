"""Wrapper único do provedor de IA (seção 3.2 do CLAUDE.md).

NUNCA instanciar um client de IA diretamente em outros arquivos — todo acesso ao
modelo passa por aqui.

Fala o protocolo **Chat Completions da OpenAI**, que é o denominador comum entre
provedores: OpenAI, Gemini (endpoint `/v1beta/openai/`), Groq, OpenRouter e o AI
Gateway da Vercel aceitam o mesmo formato. Trocar de provedor é trocar
`AI_BASE_URL` + `AI_MODEL` + `AI_API_KEY`, sem tocar em nenhum agente.
"""

import json
import re
from collections.abc import AsyncGenerator
from functools import lru_cache

import openai
import structlog
from openai import AsyncOpenAI

from core.config import settings

logger = structlog.get_logger()

AI_MODEL = settings.ai_model

# Modelo devolvendo JSON dentro de ```json ... ``` é comum fora da Anthropic.
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)


class AINotConfigured(RuntimeError):
    """AI_API_KEY ausente. Erro explícito em vez de falha obscura no request."""


@lru_cache
def _client() -> AsyncOpenAI:
    """Client preguiçoso: o SDK da OpenAI estoura na construção quando não há
    chave, e isso derrubaria a aplicação inteira no import. Adiando, um deploy
    sem chave ainda sobe e responde /health — só a tutoria falha, com log claro.
    """
    if not settings.ai_api_key:
        raise AINotConfigured(
            "AI_API_KEY não configurada — defina a chave do provedor no ambiente."
        )
    return AsyncOpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url or None,  # vazio = api.openai.com
    )


def _with_system(system_prompt: str, messages: list[dict]) -> list[dict]:
    """No protocolo da OpenAI o system prompt é a primeira mensagem, não um campo."""
    return [{"role": "system", "content": system_prompt}, *messages]


def extract_json(raw: str) -> dict:
    """Extrai o objeto JSON da resposta do modelo.

    Tolerante de propósito: modelos menores costumam cercar o JSON com bloco de
    código ou uma frase de cortesia. Tenta, em ordem: JSON puro, conteúdo de uma
    cerca ```json, e o trecho entre a primeira `{` e a última `}`.
    """
    tentativas = [raw]

    fence = _FENCE.search(raw)
    if fence:
        tentativas.append(fence.group(1))

    inicio, fim = raw.find("{"), raw.rfind("}")
    if inicio != -1 and fim > inicio:
        tentativas.append(raw[inicio : fim + 1])

    for candidato in tentativas:
        try:
            parsed = json.loads(candidato.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("O modelo não retornou JSON válido")


async def stream_tutor_response(
    system_prompt: str,
    messages: list[dict],
    student_id: str,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """Stream de resposta do modelo para a sessão de tutoria."""
    try:
        stream = await _client().chat.completions.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=_with_system(system_prompt, messages),
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            texto = chunk.choices[0].delta.content
            if texto:
                yield texto
    except openai.APIError as e:
        logger.error("ai_api_error", student_id=student_id, error=str(e))
        raise


async def complete_json(
    system_prompt: str,
    user_prompt: str,
    student_id: str,
    max_tokens: int = 2048,
) -> dict:
    """Chamada não-streaming que retorna JSON parseado.

    Pede JSON via `response_format`, mas não confia nele: provedores compatíveis
    implementam o campo de formas diferentes, e a extração cobre a diferença.
    """
    kwargs = {
        "model": AI_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        try:
            response = await _client().chat.completions.create(
                **kwargs, response_format={"type": "json_object"}
            )
        except openai.BadRequestError:
            # Provedor sem suporte a response_format: o prompt já pede JSON.
            logger.info("ai_json_mode_unsupported", model=AI_MODEL)
            response = await _client().chat.completions.create(**kwargs)
    except openai.APIError as e:
        logger.error("ai_api_error", student_id=student_id, error=str(e))
        raise

    raw = response.choices[0].message.content or ""
    try:
        return extract_json(raw)
    except ValueError:
        logger.error("ai_invalid_json", student_id=student_id, preview=raw[:200])
        raise


async def analyze_image(
    image_base64: str,
    mime_type: str,
    prompt: str,
    student_id: str,
    max_tokens: int = 2048,
) -> str:
    """Análise multimodal de imagem — usada pelo vision_agent."""
    try:
        response = await _client().chat.completions.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                        },
                    ],
                }
            ],
        )
    except openai.APIError as e:
        logger.error("ai_vision_error", student_id=student_id, error=str(e))
        raise
    return response.choices[0].message.content or ""
