"""Agregação de desempenho por aluno/matéria/dia (tabela student_performance).

Atualizado a cada evento (tentativa de exercício, sessão encerrada) em vez de
job diário — mesmo resultado, sem infraestrutura extra de cron.
"""

import uuid
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Exercise, ExerciseAttempt, StudentPerformance, Topic

MASTERY_MIN_ATTEMPTS = 3
MASTERY_RATE = 0.8
STRUGGLING_RATE = 0.4


async def _get_or_create_row(
    db: AsyncSession, student_id: uuid.UUID, subject_id: uuid.UUID | None
) -> StudentPerformance:
    today = date.today()
    row = await db.scalar(
        select(StudentPerformance).where(
            StudentPerformance.student_id == student_id,
            StudentPerformance.subject_id == subject_id,
            StudentPerformance.period_date == today,
        )
    )
    if row is None:
        row = StudentPerformance(
            student_id=student_id,
            subject_id=subject_id,
            period_date=today,
            mastered_topics=[],
            struggling_topics=[],
        )
        db.add(row)
        await db.flush()
    return row


async def _topic_mastery(
    db: AsyncSession, student_id: uuid.UUID, subject_id: uuid.UUID | None
) -> tuple[list[str], list[str]]:
    """Classifica tópicos da matéria em dominados/em dificuldade pela taxa de acerto."""
    stmt = (
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
    if subject_id is not None:
        stmt = stmt.where(Topic.subject_id == subject_id)

    mastered: list[str] = []
    struggling: list[str] = []
    for name, attempts, correct in (await db.execute(stmt)).all():
        if attempts < MASTERY_MIN_ATTEMPTS:
            continue
        rate = (correct or 0) / attempts
        if rate >= MASTERY_RATE:
            mastered.append(name)
        elif rate <= STRUGGLING_RATE:
            struggling.append(name)
    return mastered, struggling


async def record_attempt(
    db: AsyncSession,
    student_id: uuid.UUID,
    subject_id: uuid.UUID | None,
    is_correct: bool,
    score: float,
) -> None:
    row = await _get_or_create_row(db, student_id, subject_id)
    total_score = (row.avg_score or 0.0) * row.exercises_attempted + score
    row.exercises_attempted += 1
    row.exercises_correct += 1 if is_correct else 0
    row.avg_score = total_score / row.exercises_attempted
    row.mastered_topics, row.struggling_topics = await _topic_mastery(db, student_id, subject_id)


async def record_session(
    db: AsyncSession, student_id: uuid.UUID, subject_id: uuid.UUID | None
) -> None:
    row = await _get_or_create_row(db, student_id, subject_id)
    row.sessions_count += 1
