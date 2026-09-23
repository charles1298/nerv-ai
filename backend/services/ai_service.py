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

# Casa um escape JSON válido (\" \\ \/ \b \f \n \r \t \uXXXX) OU uma barra solta.
# A ordem importa: o primeiro ramo consome o par válido inteiro, então uma barra
# já escapada corretamente nunca chega ao segundo ramo.
_ESCAPE_OU_BARRA_SOLTA = re.compile(r'\\(["\\/bfnrt]|u[0-9a-fA-F]{4})|\\')


def _repara_escapes(texto: str) -> str:
    r"""Dobra as barras invertidas que não formam escape JSON válido.

    O modelo escreve LaTeX dentro das strings — `$2\%$`, `\cdot`, `R\$\,500,00` —
    e em JSON qualquer barra fora da lista de escapes válidos invalida o
    documento inteiro, não apenas aquele campo. Numa plataforma que ensina
    matemática isso não é exceção: é o conteúdo normal, e por isso a geração de
    exercícios de juros e porcentagem falhava de forma reproduzível.

    Reparar aqui é mais confiável do que pedir ao modelo que escape certo — esse
    é justamente o tipo de instrução que modelos menores esquecem.
    """
    return _ESCAPE_OU_BARRA_SOLTA.sub(
        lambda m: m.group(0) if m.group(1) else "\\\\", texto
    )


# Um trecho de matemática dentro do JSON bruto: tudo entre dois cifrões. Aspas e
# quebra de linha fechariam a string JSON antes disso, então não entram.
_MATEMATICA = re.compile(r'\$[^$"\n]*\$')

# Uma sequência de barras seguida do nome de um comando LaTeX.
_COMANDO_LATEX = re.compile(r"(\\+)([a-zA-Z]+)")


def _repara_latex(texto: str) -> str:
    r"""Protege os comandos LaTeX que o JSON engoliria em silêncio.

    `\times`, `\frac`, `\neq`, `\beta` e `\right` começam com as letras dos
    escapes válidos de JSON. O documento é aceito sem erro nenhum e o valor
    chega com um TAB no lugar de `\t` — a tela mostrava `1.200imes0,15`. Como
    nada falha, `_repara_escapes` nunca entra em cena: o conserto tem de vir
    antes da primeira tentativa de parse, não depois dela.

    Só age entre cifrões, onde toda barra é LaTeX. Fora dali `\n` é quebra de
    linha de verdade, e "preço\ne depois" não pode virar comando.

    Número ímpar de barras é o caso a corrigir. Par já está escapado certo, e
    dobrar de novo transformaria `\\frac` em quebra de linha do LaTeX.
    """

    def dobra(m: re.Match[str]) -> str:
        barras, comando = m.group(1), m.group(2)
        return (barras + "\\" if len(barras) % 2 else barras) + comando

    return _MATEMATICA.sub(lambda m: _COMANDO_LATEX.sub(dobra, m.group(0)), texto)




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
        limpo = candidato.strip()
        # O reparo de LaTeX vem primeiro porque o caso dele NÃO falha no parse:
        # a barra-t de "\times" é escape válido de JSON e viraria TAB sem erro
        # nenhum. Os outros dois só entram se o parse falhar de verdade.
        for texto in (_repara_latex(limpo), limpo, _repara_escapes(_repara_latex(limpo))):
            try:
                parsed = json.loads(texto)
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
