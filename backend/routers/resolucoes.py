"""Resolução de exercícios trazidos pelo aluno, por texto ou foto (seções 5.7 e 7.1)."""

import base64
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.resolucao_agent import (
    ResolucaoGenerationError,
    resolver_de_foto,
    resolver_de_texto,
)
from core.database import get_db
from core.security import rate_limit, require_role
from models import ExerciseSolution, User
from schemas.resolucao import (
    ResolucaoGerada,
    ResolucaoPublic,
    ResolucaoResumoPublic,
    ResolucaoTextoRequest,
)
from services.storage_service import public_url, store_file

logger = structlog.get_logger()
router = APIRouter(prefix="/resolucoes", tags=["resolucoes"])

# Mesmos limites do upload da tutoria: o gargalo é o mesmo, a foto do celular.
MIMES_ACEITOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
TAMANHO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def _to_public(registro: ExerciseSolution) -> ResolucaoPublic:
    return ResolucaoPublic(
        id=registro.id,
        origem=registro.origem,  # type: ignore[arg-type]
        enunciado=registro.enunciado,
        imagem_url=public_url(registro.imagem_key) if registro.imagem_key else None,
        enunciado_interpretado=registro.enunciado_interpretado,
        materia=registro.materia,
        topico=registro.topico,
        passos=registro.passos,
        resposta_final=registro.resposta_final,
        conceito=registro.conceito,
        erros_comuns=registro.erros_comuns,
        como_conferir=registro.como_conferir,
        exercicio_parecido=registro.exercicio_parecido,
        confianca=registro.confianca,
        created_at=registro.created_at,
    )


async def _persistir(
    db: AsyncSession,
    student: User,
    resolucao: ResolucaoGerada,
    origem: str,
    enunciado: str,
    imagem_key: str | None,
) -> ExerciseSolution:
    registro = ExerciseSolution(
        student_id=student.id,
        origem=origem,
        enunciado=enunciado,
        imagem_key=imagem_key,
        enunciado_interpretado=resolucao.enunciado_interpretado,
        materia=resolucao.materia,
        topico=resolucao.topico,
        passos=[p.model_dump() for p in resolucao.passos],
        resposta_final=resolucao.resposta_final,
        conceito=resolucao.conceito,
        erros_comuns=resolucao.erros_comuns,
        como_conferir=resolucao.como_conferir,
        exercicio_parecido=resolucao.exercicio_parecido,
        confianca=resolucao.confianca,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    logger.info(
        "exercicio_resolvido",
        resolucao_id=str(registro.id),
        student_id=str(student.id),
        origem=origem,
        materia=resolucao.materia,
        confianca=resolucao.confianca,
    )
    return registro


async def _do_aluno(
    resolucao_id: uuid.UUID, student: User, db: AsyncSession
) -> ExerciseSolution:
    """O filtro por student_id vai na query, não numa checagem depois."""
    registro = await db.scalar(
        select(ExerciseSolution).where(
            ExerciseSolution.id == resolucao_id,
            ExerciseSolution.student_id == student.id,
        )
    )
    if registro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resolução não encontrada")
    return registro


@router.post(
    "",
    response_model=ResolucaoPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("resolucao_exercicio"))],
)
async def resolver_texto(
    body: ResolucaoTextoRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> ResolucaoPublic:
    try:
        resolucao = await resolver_de_texto(student, body.enunciado, body.duvida)
    except ResolucaoGenerationError as e:
        logger.error("resolucao_falhou", origem="texto", student_id=str(student.id), error=str(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não consegui resolver esse exercício agora. Tente de novo em instantes.",
        ) from None

    registro = await _persistir(db, student, resolucao, "texto", body.enunciado.strip(), None)
    return _to_public(registro)


@router.post(
    "/foto",
    response_model=ResolucaoPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("resolucao_exercicio"))],
)
async def resolver_foto(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
    file: Annotated[UploadFile, File()],
    duvida: Annotated[str, Form()] = "",
) -> ResolucaoPublic:
    if file.content_type not in MIMES_ACEITOS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Formato não suportado. Use: {', '.join(sorted(MIMES_ACEITOS))}",
        )

    dados = await file.read()
    if not dados:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Arquivo vazio")
    if len(dados) > TAMANHO_MAXIMO:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem acima de 5 MB")

    # Guarda a foto antes de resolver: se a resolução sair errada, é a imagem que
    # explica o porquê — e sem ela o aluno não tem como mostrar o que enviou.
    imagem_key = await store_file(
        dados, file.filename or "exercicio.jpg", file.content_type, str(student.id)
    )

    try:
        resolucao = await resolver_de_foto(
            student,
            image_base64=base64.b64encode(dados).decode(),
            mime_type=file.content_type,
            duvida=duvida,
        )
    except ResolucaoGenerationError as e:
        logger.error("resolucao_falhou", origem="foto", student_id=str(student.id), error=str(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não consegui ler esse exercício na foto. Tente uma imagem mais nítida.",
        ) from None

    registro = await _persistir(db, student, resolucao, "foto", "", imagem_key)
    return _to_public(registro)


@router.get("", response_model=list[ResolucaoResumoPublic])
async def listar(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[ExerciseSolution]:
    """Histórico de exercícios resolvidos, mais recente primeiro."""
    resultado = await db.scalars(
        select(ExerciseSolution)
        .where(ExerciseSolution.student_id == student.id)
        .order_by(ExerciseSolution.created_at.desc())
    )
    return list(resultado)


@router.get("/{resolucao_id}", response_model=ResolucaoPublic)
async def obter(
    resolucao_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> ResolucaoPublic:
    return _to_public(await _do_aluno(resolucao_id, student, db))


@router.delete("/{resolucao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir(
    resolucao_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> None:
    registro = await _do_aluno(resolucao_id, student, db)
    await db.delete(registro)
    await db.commit()
    logger.info("resolucao_excluida", resolucao_id=str(resolucao_id), student_id=str(student.id))
