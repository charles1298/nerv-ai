"""Agente de cronogramas de estudo personalizados (seção 5.6 do CLAUDE.md).

O que torna o cronograma "personalizado" não é o formulário — é o cruzamento
dele com o histórico real do aluno. O formulário diz quanto tempo ele tem; o
banco diz onde ele está travando. Um plano que ignora o primeiro não é seguido;
um que ignora o segundo é só um calendário bonito.
"""

import structlog
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.estilo import ESTILO_RESPOSTA_ALUNO
from models import StudentPerformance, Subject, Topic, User
from schemas.cronograma import CronogramaCreateRequest, CronogramaGerado
from services.ai_service import complete_json

logger = structlog.get_logger()

TENTATIVAS_DE_GERACAO = 2


class CronogramaGenerationError(RuntimeError):
    """O modelo não devolveu um cronograma válido nas tentativas disponíveis."""


CRONOGRAMA_SYSTEM_PROMPT = (
    """Você é o planejador de estudos do NERV AI, especialista em rotina de estudos para
estudantes brasileiros do Ensino Fundamental e Médio, alinhado à BNCC.

Monte um cronograma realista e específico para ESTE aluno.

Regras que não podem ser quebradas:
1. O total de minutos de cada dia deve caber no tempo que o aluno informou. Nunca
   ultrapasse. É preferível um plano curto que ele cumpra do que um ambicioso que
   ele abandone na primeira semana.
2. Use exatamente o número de dias por semana informado. Não invente dias extras.
3. Priorize os tópicos em que o aluno está com dificuldade, mas sem abandonar os
   que ele domina — revisão espaçada evita que o que já foi aprendido se perca.
4. Cada bloco precisa dizer o que fazer de forma concreta ("resolver 5 questões de
   porcentagem começando pelas de nível 2"), não genérica ("estudar matemática").
5. Distribua as matérias ao longo da semana em vez de empilhar tudo num dia.
6. Nas semanas finais, aumente a proporção de simulado e revisão.
7. Use apenas matérias e tópicos da lista fornecida. Não invente conteúdo fora dela.

O campo "atividade" de cada bloco deve ser exatamente um destes valores:
revisao, exercicios, leitura, redacao, simulado, videoaula, descanso.

Responda APENAS com JSON neste formato:
{
  "resumo": "2-3 frases dizendo ao aluno o que este plano vai fazer por ele.",
  "estrategia": "Por que o plano foi montado assim, na linguagem do aluno.",
  "semanas": [
    {
      "numero": 1,
      "foco": "O que esta semana busca destravar.",
      "dias": [
        {
          "dia": "Segunda",
          "blocos": [
            {
              "materia": "Matemática",
              "topico": "Porcentagem",
              "minutos": 30,
              "atividade": "exercicios",
              "descricao": "O que fazer, concretamente."
            }
          ]
        }
      ]
    }
  ],
  "dicas": ["Conselho prático de rotina de estudo, curto e aplicável."]
}

"""
    + ESTILO_RESPOSTA_ALUNO
)


async def _contexto_do_aluno(db: AsyncSession, student: User) -> tuple[str, str]:
    """Devolve (desempenho, catálogo) — o que o banco sabe sobre este aluno.

    Sem isto o modelo geraria o mesmo cronograma genérico para qualquer aluno da
    mesma série, que é exatamente o que este recurso promete não fazer.
    """
    linhas = await db.scalars(
        select(StudentPerformance)
        .where(StudentPerformance.student_id == student.id)
        .order_by(StudentPerformance.period_date.desc())
        .limit(60)
    )

    dificuldades: list[str] = []
    dominados: list[str] = []
    acertos = tentativas = 0
    for linha in linhas:
        dificuldades.extend(linha.struggling_topics or [])
        dominados.extend(linha.mastered_topics or [])
        acertos += linha.exercises_correct or 0
        tentativas += linha.exercises_attempted or 0

    # dict.fromkeys preserva a ordem: o mais recente aparece primeiro.
    dificuldades = list(dict.fromkeys(dificuldades))[:10]
    dominados = list(dict.fromkeys(dominados))[:10]

    if tentativas:
        aproveitamento = f"{round(100 * acertos / tentativas)}% de acerto em {tentativas} exercícios"
    else:
        aproveitamento = "ainda sem exercícios respondidos"

    desempenho = (
        f"Aproveitamento: {aproveitamento}.\n"
        f"Tópicos com dificuldade: {', '.join(dificuldades) or 'nenhum registrado ainda'}.\n"
        f"Tópicos já dominados: {', '.join(dominados) or 'nenhum registrado ainda'}."
    )

    # outerjoin para a matéria sem tópico cadastrado ainda aparecer: o modelo
    # pode planejar em cima dela, mesmo sem detalhe de conteúdo.
    linhas_catalogo = await db.execute(
        select(Subject.name, Topic.name)
        .outerjoin(Topic, Topic.subject_id == Subject.id)
        .order_by(Subject.name, Topic.name)
    )
    por_materia: dict[str, list[str]] = {}
    for materia, topico in linhas_catalogo:
        por_materia.setdefault(materia, [])
        if topico:
            por_materia[materia].append(topico)

    catalogo = "\n".join(
        f"- {materia}: {', '.join(topicos) or 'sem tópicos cadastrados'}"
        for materia, topicos in por_materia.items()
    )

    return desempenho, catalogo or "- catálogo vazio"


def _monta_prompt(
    student: User, pedido: CronogramaCreateRequest, desempenho: str, catalogo: str
) -> str:
    materias = ", ".join(pedido.materias) if pedido.materias else "o aluno não restringiu"
    return (
        f"Aluno: {student.name}\n"
        f"Série: {student.grade or 'não informada'}\n\n"
        f"Objetivo: {pedido.objetivo}\n"
        f"Duração do plano: {pedido.semanas} semana(s)\n"
        f"Dias de estudo por semana: {pedido.dias_por_semana}\n"
        f"Tempo disponível por dia: {pedido.minutos_por_dia} minutos\n"
        f"Matérias que o aluno quer priorizar: {materias}\n\n"
        f"Desempenho registrado:\n{desempenho}\n\n"
        f"Catálogo de matérias e tópicos disponíveis:\n{catalogo}"
    )


async def gerar_cronograma(
    db: AsyncSession, student: User, pedido: CronogramaCreateRequest
) -> CronogramaGerado:
    """Gera e valida o cronograma. Levanta CronogramaGenerationError se não vier válido."""
    desempenho, catalogo = await _contexto_do_aluno(db, student)
    prompt = _monta_prompt(student, pedido, desempenho, catalogo)

    ultimo_erro: Exception | None = None
    correcao = ""

    for tentativa in range(1, TENTATIVAS_DE_GERACAO + 1):
        try:
            raw = await complete_json(
                system_prompt=CRONOGRAMA_SYSTEM_PROMPT,
                user_prompt=prompt + correcao,
                student_id=str(student.id),
                max_tokens=4096,
            )
            plano = CronogramaGerado.model_validate(raw)
        except (ValueError, ValidationError) as e:
            ultimo_erro = e
            logger.warning(
                "cronograma_invalido", tentativa=tentativa, de=TENTATIVAS_DE_GERACAO, error=str(e)
            )
            continue

        estourados = plano.dias_acima_do_orcamento(pedido.minutos_por_dia)
        if not estourados:
            return plano

        # Estourar o tempo do aluno é falha de conteúdo, não de formato: o JSON
        # está válido, mas o plano é inaplicável. Vale uma segunda chamada
        # apontando os dias exatos — instrução genérica o modelo já ignorou uma vez.
        logger.warning(
            "cronograma_acima_do_orcamento",
            tentativa=tentativa,
            minutos_por_dia=pedido.minutos_por_dia,
            dias=estourados[:5],
        )
        if tentativa == TENTATIVAS_DE_GERACAO:
            # Melhor entregar um plano apertado do que nenhum: o aluno consegue
            # cortar um bloco, mas não consegue usar uma tela de erro.
            return plano

        correcao = (
            f"\n\nATENÇÃO: a tentativa anterior estourou o tempo do aluno nestes dias: "
            f"{'; '.join(estourados[:5])}. O limite é {pedido.minutos_por_dia} minutos por dia, "
            f"somando todos os blocos daquele dia. Refaça respeitando o limite."
        )

    raise CronogramaGenerationError("O modelo não devolveu um cronograma válido") from ultimo_erro

