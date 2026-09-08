"""Cronogramas de estudo personalizados (seções 5.6 e 7.1)."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.cronograma_agent import CronogramaGenerationError, gerar_cronograma
from core.database import get_db
from core.security import rate_limit, require_role
from models import StudyPlan, User
from schemas.cronograma import (
    CronogramaCreateRequest,
    CronogramaPublic,
    CronogramaResumoPublic,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/cronogramas", tags=["cronogramas"])


async def _plano_do_aluno(plano_id: uuid.UUID, student: User, db: AsyncSession) -> StudyPlan:
    """Busca o plano garantindo que ele é do aluno autenticado.

    O filtro por student_id vai na query, não numa checagem depois: assim o
    cronograma de um aluno nunca é carregado no processo por conta de outro.
    """
    plano = await db.scalar(
        select(StudyPlan).where(StudyPlan.id == plano_id, StudyPlan.student_id == student.id)
    )
    if plano is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cronograma não encontrado")
    return plano


@router.post(
    "",
    response_model=CronogramaPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("cronograma_generation"))],
)
async def criar_cronograma(
    body: CronogramaCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> StudyPlan:
    try:
        gerado = await gerar_cronograma(db, student, body)
    except CronogramaGenerationError as e:
        logger.error("cronograma_generation_failed", student_id=str(student.id), error=str(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não consegui montar seu cronograma agora. Tente de novo em instantes.",
        ) from None

    plano = StudyPlan(
        student_id=student.id,
        objetivo=body.objetivo,
        semanas_total=body.semanas,
        dias_por_semana=body.dias_por_semana,
        minutos_por_dia=body.minutos_por_dia,
        materias_foco=body.materias,
        resumo=gerado.resumo,
        estrategia=gerado.estrategia,
        semanas=[s.model_dump() for s in gerado.semanas],
        dicas=gerado.dicas,
    )
    db.add(plano)
    await db.commit()
    await db.refresh(plano)
    logger.info(
        "cronograma_criado",
        plano_id=str(plano.id),
        student_id=str(student.id),
        semanas=body.semanas,
        minutos_por_dia=body.minutos_por_dia,
    )
    return plano


@router.get("", response_model=list[CronogramaResumoPublic])
async def listar_cronogramas(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[StudyPlan]:
    """Histórico de cronogramas, mais recente primeiro (sem o corpo do plano)."""
    result = await db.scalars(
        select(StudyPlan)
        .where(StudyPlan.student_id == student.id)
        .order_by(StudyPlan.created_at.desc())
    )
    return list(result)


@router.get("/{plano_id}", response_model=CronogramaPublic)
async def obter_cronograma(
    plano_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> StudyPlan:
    return await _plano_do_aluno(plano_id, student, db)


@router.delete("/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_cronograma(
    plano_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> None:
    plano = await _plano_do_aluno(plano_id, student, db)
    await db.delete(plano)
    await db.commit()
    logger.info("cronograma_excluido", plano_id=str(plano_id), student_id=str(student.id))
