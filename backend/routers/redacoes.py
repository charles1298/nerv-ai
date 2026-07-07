"""Submissão e histórico de redações com avaliação ENEM (seções 5.3 e 7.1)."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.redacao_agent import evaluate_essay
from core.database import get_db
from core.security import rate_limit, require_role
from models import Essay, User
from schemas.redacao import EssayPublic, RedacaoSubmitRequest
from services.gamification_service import award_xp

logger = structlog.get_logger()
router = APIRouter(prefix="/redacoes", tags=["redacoes"])


@router.post(
    "",
    response_model=EssayPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("redacao_submission"))],
)
async def submit_essay(
    body: RedacaoSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> Essay:
    try:
        avaliacao = await evaluate_essay(student, body.theme, body.content)
    except Exception as e:
        logger.error("essay_evaluation_failed", student_id=str(student.id), error=str(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Falha na correção. Tente novamente em instantes."
        ) from e

    essay = Essay(
        student_id=student.id,
        theme=body.theme,
        content=body.content,
        nota_total=avaliacao.nota_total,
        notas_por_criterio=avaliacao.notas_por_criterio,
        analise_detalhada=avaliacao.analise_detalhada.model_dump(),
        reescrita_sugerida=avaliacao.reescrita_sugerida,
        nota_estimada_real_enem=avaliacao.nota_estimada_real_enem,
        proximos_passos=avaliacao.proximos_passos,
    )
    db.add(essay)
    await db.flush()

    await award_xp(db, student.id, "redacao_submetida")
    if avaliacao.nota_total >= 800:
        await award_xp(db, student.id, "redacao_acima_de_800")

    await db.commit()
    await db.refresh(essay)
    return essay


@router.get("", response_model=list[EssayPublic])
async def list_essays(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[Essay]:
    """Histórico de redações com evolução de notas (mais recente primeiro)."""
    result = await db.scalars(
        select(Essay).where(Essay.student_id == student.id).order_by(Essay.submitted_at.desc())
    )
    return list(result)
