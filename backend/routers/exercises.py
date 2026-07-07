"""Geração e tentativas de exercícios (Fase 1: correção local de múltipla escolha)."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.exercise_agent import generate_exercise, grade_multiple_choice
from core.database import get_db
from core.security import rate_limit, require_role
from models import Exercise, ExerciseAttempt, Topic, User
from services.gamification_service import award_xp
from services.performance_service import record_attempt
from schemas.exercises import (
    AttemptRequest,
    AttemptResult,
    ExerciseContent,
    ExerciseGenerateRequest,
    ExercisePublic,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/exercises", tags=["exercises"])


def _to_public(exercise: Exercise) -> ExercisePublic:
    """Remove gabarito e solução antes de expor ao aluno."""
    content = ExerciseContent.model_validate(exercise.content)
    return ExercisePublic(
        id=exercise.id,
        topic_id=exercise.topic_id,
        question=content.question,
        tipo=exercise.tipo,
        difficulty=exercise.difficulty,
        alternatives=[{"label": a.label, "text": a.text} for a in content.alternatives],
        hints=content.hints,
        created_at=exercise.created_at,
    )


@router.post(
    "/generate",
    response_model=ExercisePublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("exercise_generation"))],
)
async def generate(
    body: ExerciseGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> ExercisePublic:
    topic = await db.scalar(
        select(Topic).options(selectinload(Topic.subject)).where(Topic.id == body.topic_id)
    )
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tópico não encontrado")
    exercise = await generate_exercise(db, student, topic, body.tipo)
    return _to_public(exercise)


@router.get("", response_model=list[ExercisePublic])
async def list_exercises(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[ExercisePublic]:
    result = await db.scalars(
        select(Exercise)
        .where(Exercise.student_id == student.id)
        .order_by(Exercise.created_at.desc())
        .limit(50)
    )
    return [_to_public(e) for e in result]


@router.post("/{exercise_id}/attempt", response_model=AttemptResult)
async def attempt(
    exercise_id: uuid.UUID,
    body: AttemptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> AttemptResult:
    exercise = await db.scalar(
        select(Exercise).where(Exercise.id == exercise_id, Exercise.student_id == student.id)
    )
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercício não encontrado")
    if exercise.tipo != "multipla_escolha":
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED,
            "Correção automática deste tipo chega na Fase 2 (redacao_agent)",
        )

    is_correct, score, feedback = grade_multiple_choice(exercise, body.answer)

    # Gamificação: XP por acerto na 1ª ou 2ª tentativa (seção 8)
    previous_attempts = await db.scalar(
        select(func.count(ExerciseAttempt.id)).where(
            ExerciseAttempt.exercise_id == exercise.id,
            ExerciseAttempt.student_id == student.id,
        )
    )
    if is_correct and previous_attempts == 0:
        await award_xp(db, student.id, "exercicio_correto_primeira_tentativa")
    elif is_correct and previous_attempts == 1:
        await award_xp(db, student.id, "exercicio_correto_segunda_tentativa")

    topic = await db.scalar(select(Topic).where(Topic.id == exercise.topic_id))
    await record_attempt(
        db, student.id, topic.subject_id if topic else None, is_correct, score
    )

    record = ExerciseAttempt(
        exercise_id=exercise.id,
        student_id=student.id,
        answer=body.answer,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
        time_spent_seconds=body.time_spent_seconds,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    logger.info(
        "exercise_attempted",
        exercise_id=str(exercise.id),
        student_id=str(student.id),
        is_correct=is_correct,
    )
    content = ExerciseContent.model_validate(exercise.content)
    return AttemptResult(
        attempt_id=record.id,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
        step_by_step_solution=content.step_by_step_solution,
    )
