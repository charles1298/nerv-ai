"""LGPD — exportação e deleção de dados pessoais (Fase 3, seção 10).

Exportação: aluno baixa todos os próprios dados em JSON.
Deleção: anonimiza o usuário e apaga conteúdo pessoal (mensagens, redações,
uploads), preservando agregados estatísticos anonimizados da escola.
"""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user, require_role
from models import (
    Essay,
    Exercise,
    ExerciseAttempt,
    SessionMessage,
    StudentGamification,
    TutoringSession,
    Upload,
    User,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/lgpd", tags=["lgpd"])


async def _collect_student_data(db: AsyncSession, student: User) -> dict:
    sessions = (
        await db.scalars(
            select(TutoringSession).where(TutoringSession.student_id == student.id)
        )
    ).all()
    session_ids = [s.id for s in sessions]
    messages = []
    if session_ids:
        messages = (
            await db.scalars(
                select(SessionMessage).where(SessionMessage.session_id.in_(session_ids))
            )
        ).all()
    essays = (await db.scalars(select(Essay).where(Essay.student_id == student.id))).all()
    attempts = (
        await db.scalars(
            select(ExerciseAttempt).where(ExerciseAttempt.student_id == student.id)
        )
    ).all()
    uploads = (await db.scalars(select(Upload).where(Upload.student_id == student.id))).all()

    return {
        "user": {
            "id": str(student.id),
            "name": student.name,
            "email": student.email,
            "grade": student.grade,
            "created_at": student.created_at.isoformat(),
        },
        "sessions": [
            {
                "id": str(s.id),
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "insights": s.insights,
            }
            for s in sessions
        ],
        "messages": [
            {"session_id": str(m.session_id), "role": m.role, "content": m.content}
            for m in messages
        ],
        "essays": [
            {"theme": e.theme, "content": e.content, "nota_total": e.nota_total}
            for e in essays
        ],
        "exercise_attempts": [
            {
                "exercise_id": str(a.exercise_id),
                "answer": a.answer,
                "is_correct": a.is_correct,
                "score": a.score,
            }
            for a in attempts
        ],
        "uploads": [{"filename": u.filename, "uploaded_at": u.uploaded_at.isoformat()} for u in uploads],
    }


async def _erase_student_data(db: AsyncSession, student: User) -> None:
    session_ids = (
        await db.scalars(
            select(TutoringSession.id).where(TutoringSession.student_id == student.id)
        )
    ).all()
    if session_ids:
        await db.execute(delete(SessionMessage).where(SessionMessage.session_id.in_(session_ids)))
    await db.execute(delete(Essay).where(Essay.student_id == student.id))
    await db.execute(delete(Upload).where(Upload.student_id == student.id))
    await db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.student_id == student.id))
    await db.execute(delete(Exercise).where(Exercise.student_id == student.id))
    await db.execute(delete(TutoringSession).where(TutoringSession.student_id == student.id))
    await db.execute(
        delete(StudentGamification).where(StudentGamification.student_id == student.id)
    )

    # Anonimização: mantém a linha (integridade referencial), remove dados pessoais
    student.name = "Usuário removido"
    student.email = f"removido-{student.id}@anonimizado.nerv.ai"
    student.password_hash = "!"
    student.avatar_url = None
    await db.commit()
    logger.info("lgpd_erasure_completed", user_id=str(student.id))


@router.get("/export")
async def export_my_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Aluno (ou qualquer usuário) exporta os próprios dados."""
    return await _collect_student_data(db, current)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    """Usuário solicita deleção dos próprios dados (direito ao esquecimento)."""
    await _erase_student_data(db, current)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_data(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("admin", "manager"))],
) -> None:
    """Gestor/admin deleta dados de um aluno da própria escola (pedido do responsável)."""
    student = await db.scalar(
        select(User).where(
            User.id == student_id,
            User.school_id == current.school_id,
            User.role == "student",
        )
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aluno não encontrado")
    await _erase_student_data(db, student)
