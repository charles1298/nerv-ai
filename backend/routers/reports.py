"""Relatórios pedagógicos para professores e gestores (seções 5.5, 7.2, 7.3).

Isolamento multi-tenant: todas as queries filtram por school_id do usuário logado.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.report_agent import generate_student_report
from core.database import get_db
from core.security import require_role
from models import (
    Essay,
    Exercise,
    ExerciseAttempt,
    Subject,
    Topic,
    TutoringSession,
    User,
)
from services.notification_service import send_email
from services.performance_service import MASTERY_MIN_ATTEMPTS, MASTERY_RATE

logger = structlog.get_logger()
router = APIRouter(prefix="/reports", tags=["reports"])

ATTENTION_RATE = 0.6
CRITICAL_RATE = 0.4
INACTIVE_DAYS = 7


async def _get_school_student(
    db: AsyncSession, student_id: uuid.UUID, current: User
) -> User:
    """Carrega o aluno garantindo que pertence à escola do solicitante."""
    student = await db.scalar(
        select(User).where(
            User.id == student_id,
            User.school_id == current.school_id,
            User.role == "student",
        )
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aluno não encontrado")
    return student


async def _student_aggregates(db: AsyncSession, student_id: uuid.UUID) -> dict:
    """Agregados de desempenho de um aluno (fonte para status e relatórios)."""
    sessions_count = await db.scalar(
        select(func.count(TutoringSession.id)).where(TutoringSession.student_id == student_id)
    )
    last_session = await db.scalar(
        select(func.max(TutoringSession.started_at)).where(
            TutoringSession.student_id == student_id
        )
    )
    attempts_row = (
        await db.execute(
            select(
                func.count(ExerciseAttempt.id),
                func.sum(case((ExerciseAttempt.is_correct.is_(True), 1), else_=0)),
                func.avg(ExerciseAttempt.score),
            ).where(ExerciseAttempt.student_id == student_id)
        )
    ).one()
    attempts, correct, avg_score = attempts_row

    topic_rows = (
        await db.execute(
            select(
                Topic.name,
                func.count(ExerciseAttempt.id),
                func.sum(case((ExerciseAttempt.is_correct.is_(True), 1), else_=0)),
            )
            .join(Exercise, Exercise.topic_id == Topic.id)
            .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
            .where(ExerciseAttempt.student_id == student_id)
            .group_by(Topic.id, Topic.name)
        )
    ).all()
    mastered = [
        name
        for name, total, ok in topic_rows
        if total >= MASTERY_MIN_ATTEMPTS and (ok or 0) / total >= MASTERY_RATE
    ]
    struggling = [
        name
        for name, total, ok in topic_rows
        if total >= MASTERY_MIN_ATTEMPTS and (ok or 0) / total <= CRITICAL_RATE
    ]

    best_essay = await db.scalar(
        select(func.max(Essay.nota_total)).where(Essay.student_id == student_id)
    )

    correct_rate = (correct or 0) / attempts if attempts else None
    return {
        "sessions_count": sessions_count or 0,
        "last_session_at": last_session.isoformat() if last_session else None,
        "exercises_attempted": attempts or 0,
        "exercises_correct": int(correct or 0),
        "correct_rate": round(correct_rate, 2) if correct_rate is not None else None,
        "avg_score": round(float(avg_score), 1) if avg_score is not None else None,
        "mastered_topics": mastered,
        "struggling_topics": struggling,
        "best_essay_score": best_essay,
    }


def _status_from_aggregates(agg: dict) -> str:
    """em_dia | atencao | critico — ordena a necessidade de intervenção (seção 7.2)."""
    last = agg["last_session_at"]
    inactive = last is None or (
        datetime.now(timezone.utc) - datetime.fromisoformat(last)
    ) > timedelta(days=INACTIVE_DAYS)
    rate = agg["correct_rate"]

    if (rate is not None and rate < CRITICAL_RATE) or (inactive and agg["sessions_count"] == 0):
        return "critico"
    if (rate is not None and rate < ATTENTION_RATE) or inactive or agg["struggling_topics"]:
        return "atencao"
    return "em_dia"


@router.get("/turma")
async def class_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
) -> list[dict]:
    """Cards por aluno ordenados por necessidade de intervenção."""
    students = await db.scalars(
        select(User).where(User.school_id == current.school_id, User.role == "student")
    )
    cards = []
    for student in students:
        agg = await _student_aggregates(db, student.id)
        cards.append(
            {
                "student_id": str(student.id),
                "name": student.name,
                "grade": student.grade,
                "status": _status_from_aggregates(agg),
                **agg,
            }
        )
    order = {"critico": 0, "atencao": 1, "em_dia": 2}
    cards.sort(key=lambda c: (order[c["status"]], c["name"]))
    return cards


@router.get("/aluno/{student_id}")
async def student_report(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
) -> dict:
    """Relatório individual: agregados do banco + narrativa do report_agent."""
    student = await _get_school_student(db, student_id, current)
    agg = await _student_aggregates(db, student.id)
    try:
        narrative = await generate_student_report(student.name, student.grade, agg)
    except Exception as e:
        logger.warning("report_narrative_failed", student_id=str(student_id), error=str(e))
        narrative = None
    return {
        "student": {"id": str(student.id), "name": student.name, "grade": student.grade},
        "aggregates": agg,
        "status": _status_from_aggregates(agg),
        "narrative": narrative,
    }


@router.get("/alertas")
async def alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
    notify: bool = False,
) -> list[dict]:
    """Alunos com dificuldade persistente. Com notify=true, envia e-mail ao solicitante."""
    cards = await class_dashboard(db, current)
    flagged = [c for c in cards if c["status"] in ("critico", "atencao")]

    if notify and flagged:
        rows = "".join(
            f"<li><b>{c['name']}</b> ({c['status']}): "
            f"tópicos em dificuldade: {', '.join(c['struggling_topics']) or 'inatividade'}</li>"
            for c in flagged
        )
        await send_email(
            to=current.email,
            subject=f"NERV AI — {len(flagged)} aluno(s) precisando de atenção",
            html=f"<p>Alunos identificados pelo NERV:</p><ul>{rows}</ul>",
        )
    return flagged


@router.get("/escola")
async def school_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("manager", "admin"))],
) -> dict:
    """Mapa de desempenho por série/matéria para o gestor (seção 7.3)."""
    rows = (
        await db.execute(
            select(
                User.grade,
                Subject.name,
                func.count(ExerciseAttempt.id),
                func.sum(case((ExerciseAttempt.is_correct.is_(True), 1), else_=0)),
            )
            .join(ExerciseAttempt, ExerciseAttempt.student_id == User.id)
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .join(Topic, Topic.id == Exercise.topic_id)
            .join(Subject, Subject.id == Topic.subject_id)
            .where(User.school_id == current.school_id, User.role == "student")
            .group_by(User.grade, Subject.id, Subject.name)
        )
    ).all()

    heatmap = [
        {
            "grade": grade,
            "subject": subject_name,
            "attempts": attempts,
            "correct_rate": round((correct or 0) / attempts, 2) if attempts else None,
        }
        for grade, subject_name, attempts, correct in rows
    ]

    students_count = await db.scalar(
        select(func.count(User.id)).where(
            User.school_id == current.school_id, User.role == "student"
        )
    )
    active_week = await db.scalar(
        select(func.count(distinct(TutoringSession.student_id)))
        .join(User, User.id == TutoringSession.student_id)
        .where(
            User.school_id == current.school_id,
            TutoringSession.started_at >= datetime.now(timezone.utc) - timedelta(days=7),
        )
    )
    return {
        "students_count": students_count or 0,
        "active_students_last_7_days": active_week or 0,
        "heatmap": heatmap,
    }


@router.get("/bncc")
async def bncc_diagnostic(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
) -> list[dict]:
    """% de habilidades BNCC dominadas por matéria na escola (seção 5.5)."""
    subjects = (await db.scalars(select(Subject))).all()
    result = []
    for subject in subjects:
        topics = (await db.scalars(select(Topic).where(Topic.subject_id == subject.id))).all()
        if not topics:
            continue
        mastered_count = 0
        for topic in topics:
            row = (
                await db.execute(
                    select(
                        func.count(ExerciseAttempt.id),
                        func.sum(case((ExerciseAttempt.is_correct.is_(True), 1), else_=0)),
                    )
                    .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
                    .join(User, User.id == ExerciseAttempt.student_id)
                    .where(Exercise.topic_id == topic.id, User.school_id == current.school_id)
                )
            ).one()
            attempts, correct = row
            if attempts and attempts >= MASTERY_MIN_ATTEMPTS and (correct or 0) / attempts >= MASTERY_RATE:
                mastered_count += 1
        result.append(
            {
                "subject": subject.name,
                "bncc_code": subject.bncc_code,
                "topics_total": len(topics),
                "topics_mastered": mastered_count,
                "mastery_pct": round(mastered_count / len(topics) * 100, 1),
            }
        )
    return result
