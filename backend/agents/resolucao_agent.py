"""Agente de resolução de exercícios (seção 5.7 do CLAUDE.md).

Este é o único agente do NERV que **entrega a resposta**. O tutor foi construído
para nunca fazer isso — ele guia o aluno até a descoberta. A exceção existe
porque o aluno chega com a lista da escola travado num exercício, e nesse
momento o guia socrático não resolve: ele já tentou e não saiu do lugar.

Para isso não virar máquina de fazer lição de casa, a resposta nunca vem sozinha.
Vem com o porquê de cada passo, o conceito por trás, os erros comuns daquele tipo
de questão, como conferir o resultado e um exercício parecido para o aluno fazer
sozinho. Quem só quer copiar a resposta consegue; quem quer aprender tem por onde.
"""

import structlog
from pydantic import ValidationError

from agents.estilo import ESTILO_RESPOSTA_ALUNO
from models import User
from schemas.resolucao import ResolucaoGerada
from services.ai_service import analyze_image, complete_json, extract_json

logger = structlog.get_logger()

TENTATIVAS = 2


class ResolucaoGenerationError(RuntimeError):
    """O modelo não devolveu uma resolução válida nas tentativas disponíveis."""


# String raw: a instrucao cita comandos LaTeX como \times. Sem o r, o \t viraria
# TAB de verdade e o modelo leria "multiplicacao e <TAB>imes".
_FORMATO = r"""Responda APENAS com JSON neste formato:
{
  "enunciado_interpretado": "O exercício, escrito por você, do jeito que entendeu.",
  "materia": "Matemática",
  "topico": "Teorema de Pitágoras",
  "passos": [
    {
      "numero": 1,
      "titulo": "Título curto do que se faz neste passo",
      "explicacao": "Por que este passo existe e como ele se faz.",
      "expressao": "$a^2 = b^2 + c^2$"
    }
  ],
  "resposta_final": "A resposta, direta.",
  "conceito": "O conceito por trás, explicado para quem ainda não entendeu.",
  "erros_comuns": ["O erro que mais aparece neste tipo de questão."],
  "como_conferir": "Como o aluno verifica sozinho se o resultado faz sentido.",
  "exercicio_parecido": "Um exercício parecido, com os números trocados, para praticar.",
  "confianca": "alta"
}

Regras do conteúdo:
- Resolva por completo. O aluno veio aqui justamente porque travou.
- Cada passo explica o PORQUÊ, não só a conta. "Elevamos os dois lados ao
  quadrado para eliminar a raiz" ensina; "elevando ao quadrado" não ensina nada.
- Quebre em passos pequenos. É melhor seis passos curtos que dois enormes.
- "expressao" leva só a conta daquele passo, SEMPRE em LaTeX inline entre $...$.
  Se o passo não tem conta (interpretar o enunciado, por exemplo), deixe null.
  Escreva como se escreve no caderno: multiplicação é \times ou \cdot, nunca
  asterisco; divisão é \div ou fração; decimal com vírgula, como 0{,}15.
  Exemplo bom: "$800 \times 0{,}15 = 120$". Exemplo ruim: "800 * 0,15 = 120".
- "conceito" é o que o aluno precisa entender para resolver sozinho o próximo.
- "confianca" é sua honestidade sobre a leitura do enunciado: use "baixa" quando
  faltar informação ou a imagem estiver ilegível, e diga em
  "enunciado_interpretado" o que conseguiu ler. Nunca invente dados que faltam.

"""

SYSTEM_PROMPT_TEXTO = (
    """Você é o resolvedor de exercícios do NERV AI, para estudantes brasileiros do
Ensino Fundamental e Médio, alinhado à BNCC.

O aluno trouxe um exercício e quer entender como se resolve.

"""
    + _FORMATO
    + ESTILO_RESPOSTA_ALUNO
)

PROMPT_FOTO = (
    """Você é o resolvedor de exercícios do NERV AI, para estudantes brasileiros do
Ensino Fundamental e Médio, alinhado à BNCC.

O aluno fotografou um exercício. Leia a imagem, identifique o exercício e resolva.

Se a foto tiver vários exercícios, resolva o primeiro e diga em
"enunciado_interpretado" que havia outros. Se estiver ilegível, não chute: use
confianca "baixa" e escreva o que conseguiu ler.

"""
    + _FORMATO
    + ESTILO_RESPOSTA_ALUNO
)


def _contexto(student: User, duvida: str) -> str:
    partes = [
        f"Série do aluno: {student.grade or 'não informada'}.",
    ]
    if duvida.strip():
        # A dúvida específica muda o foco: explicar tudo de novo para quem já
        # entendeu metade é ruído.
        partes.append(f"O aluno disse onde travou: {duvida.strip()}")
    return " ".join(partes)


def _valida(bruto: dict) -> ResolucaoGerada:
    resolucao = ResolucaoGerada.model_validate(bruto)
    # Renumera antes de persistir: a tela mostra o número em destaque.
    return resolucao.model_copy(update={"passos": resolucao.passos_ordenados()})


async def resolver_de_texto(student: User, enunciado: str, duvida: str = "") -> ResolucaoGerada:
    user_prompt = f"{_contexto(student, duvida)}\n\nExercício:\n{enunciado.strip()}"

    ultimo_erro: Exception | None = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            bruto = await complete_json(
                system_prompt=SYSTEM_PROMPT_TEXTO,
                user_prompt=user_prompt,
                student_id=str(student.id),
                max_tokens=4096,
            )
            return _valida(bruto)
        except (ValueError, ValidationError) as e:
            ultimo_erro = e
            logger.warning("resolucao_invalida", origem="texto", tentativa=tentativa, error=str(e))

    raise ResolucaoGenerationError("O modelo não devolveu uma resolução válida") from ultimo_erro


async def resolver_de_foto(
    student: User, image_base64: str, mime_type: str, duvida: str = ""
) -> ResolucaoGerada:
    prompt = f"{PROMPT_FOTO}\n\n{_contexto(student, duvida)}"

    ultimo_erro: Exception | None = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            # A chamada de visão devolve texto; o extract_json é o mesmo do resto
            # do sistema, já tolerante a cerca de código e a LaTeX dentro do JSON.
            texto = await analyze_image(
                image_base64=image_base64,
                mime_type=mime_type,
                prompt=prompt,
                student_id=str(student.id),
                max_tokens=4096,
            )
            return _valida(extract_json(texto))
        except (ValueError, ValidationError) as e:
            ultimo_erro = e
            logger.warning("resolucao_invalida", origem="foto", tentativa=tentativa, error=str(e))

    raise ResolucaoGenerationError("O modelo não devolveu uma resolução válida") from ultimo_erro
