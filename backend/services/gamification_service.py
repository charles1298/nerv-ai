"""Gamificação — XP, streak e badges (seção 8 do CLAUDE.md)."""

import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Essay,
    Exercise,
    ExerciseAttempt,
    StudentGamification,
    Subject,
    Topic,
    TutoringSession,
)

logger = structlog.get_logger()

XP_RULES: dict[str, int] = {
    "sessao_completada": 50,
    "exercicio_correto_primeira_tentativa": 30,
    "exercicio_correto_segunda_tentativa": 15,
    "redacao_submetida": 40,
    "redacao_acima_de_800": 100,
    "streak_7_dias": 200,
    "streak_30_dias": 1000,
    "topico_dominado": 150,
    "modulo_completado": 500,
}

BADGES: list[dict] = [
    {"id": "primeira_sessao", "name": "Início de Jornada", "xp_reward": 50},
    {"id": "matematico", "name": "Mente Matemática", "condition": "10 exercícios de mat corretos"},
    {"id": "escritor", "name": "Redator ENEM", "condition": "nota 800+ em redação"},
    {"id": "estudioso", "name": "Dedicação Total", "condition": "30 dias de streak"},
    {"id": "explorador", "name": "Curioso Nato", "condition": "5 matérias diferentes em 1 semana"},
    {"id": "mestre_bncc", "name": "Mestre BNCC", "condition": "100% de habilidades EF dominadas"},
]

BADGES_BY_ID = {b["id"]: b for b in BADGES}


async def get_or_create_gamification(db: AsyncSession, student_id: uuid.UUID) -> StudentGamification:
    gam = await db.scalar(
        select(StudentGamification).where(StudentGamification.student_id == student_id)
    )
    if gam is None:
        gam = StudentGamification(student_id=student_id, badges=[])
        db.add(gam)
        await db.flush()
    return gam


def _update_streak(gam: StudentGamification) -> int:
    """Atualiza o streak com base na data da última atividade. Retorna XP de streak ganho."""
    today = date.today()
    if gam.last_activity_date == today:
        return 0
    if gam.last_activity_date == today - timedelta(days=1):
        gam.streak_days += 1
    else:
        gam.streak_days = 1
    gam.last_activity_date = today

    if gam.streak_days == 7:
        return XP_RULES["streak_7_dias"]
    if gam.streak_days == 30:
        return XP_RULES["streak_30_dias"]
    return 0


async def _check_new_badges(
    db: AsyncSession, student_id: uuid.UUID, gam: StudentGamification
) -> list[str]:
    """Avalia condições de badges ainda não conquistadas."""
    earned = set(gam.badges or [])
    new_badges: list[str] = []
    week_ago = date.today() - timedelta(days=7)

    if "primeira_sessao" not in earned:
        sessions = await db.scalar(
            select(func.count(TutoringSession.id)).where(TutoringSession.student_id == student_id)
        )
        if sessions and sessions >= 1:
            new_badges.append("primeira_sessao")

    if "matematico" not in earned:
        math_correct = await db.scalar(
            select(func.count(ExerciseAttempt.id))
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .join(Topic, Topic.id == Exercise.topic_id)
            .join(Subject, Subject.id == Topic.subject_id)
            .where(
                ExerciseAttempt.student_id == student_id,
                ExerciseAttempt.is_correct.is_(True),
                Subject.bncc_code == "MT",
            )
        )
        if math_correct and math_correct >= 10:
            new_badges.append("matematico")

    if "escritor" not in earned:
        best_essay = await db.scalar(
            select(func.max(Essay.nota_total)).where(Essay.student_id == student_id)
        )
        if best_essay is not None and best_essay >= 800:
            new_badges.append("escritor")

    if "estudioso" not in earned and gam.streak_days >= 30:
        new_badges.append("estudioso")

    if "explorador" not in earned:
        subjects_this_week = await db.scalar(
            select(func.count(distinct(Topic.subject_id)))
            .join(Exercise, Exercise.topic_id == Topic.id)
            .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
            .where(
                ExerciseAttempt.student_id == student_id,
                ExerciseAttempt.attempted_at >= week_ago,
            )
        )
        if subjects_this_week and subjects_this_week >= 5:
            new_badges.append("explorador")

    return new_badges


async def award_xp(db: AsyncSession, student_id: uuid.UUID, event: str) -> StudentGamification:
    """Registra atividade, concede XP do evento, atualiza streak e badges.

    Commit fica a cargo do chamador (participa da transação do request).
    """
    gam = await get_or_create_gamification(db, student_id)
    gam.xp_total += XP_RULES.get(event, 0)
    gam.xp_total += _update_streak(gam)

    new_badges = await _check_new_badges(db, student_id, gam)
    for badge_id in new_badges:
        gam.badges = [*(gam.badges or []), badge_id]
        gam.xp_total += int(BADGES_BY_ID[badge_id].get("xp_reward", 0))
        logger.info("badge_earned", student_id=str(student_id), badge=badge_id)

    return gam
