"""Teste manual do ciclo dos agentes contra a Claude API real (seção 13).

Requer AI_API_KEY válida e banco de pé. Uso (a partir de backend/):
    python ../scripts/test_agents.py --student-email aluno@demo.nerv.ai --subject Matemática --topic "Funções quadráticas"
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from agents.exercise_agent import generate_exercise
from agents.tutor_agent import run_tutor_turn
from core.database import async_session_maker, engine
from models import Subject, Topic, TutoringSession, User

logger = structlog.get_logger()


async def main(student_email: str, subject_name: str, topic_name: str) -> None:
    async with async_session_maker() as db:
        student = await db.scalar(select(User).where(User.email == student_email))
        if student is None:
            logger.error("student_not_found", email=student_email)
            return

        subject = await db.scalar(select(Subject).where(Subject.name == subject_name))
        topic = await db.scalar(
            select(Topic)
            .options(selectinload(Topic.subject))
            .where(Topic.name == topic_name)
        )
        if subject is None or topic is None:
            logger.error("subject_or_topic_not_found", subject=subject_name, topic=topic_name)
            return

        # 1. Sessão de tutoria com streaming
        session = TutoringSession(student_id=student.id, subject_id=subject.id, topic_id=topic.id)
        db.add(session)
        await db.commit()
        await db.refresh(session, attribute_names=["subject", "topic"])

        logger.info("tutor_turn_start", session_id=str(session.id))
        chunks: list[str] = []
        async for chunk in run_tutor_turn(
            student, session, [], f"Me explica o básico de {topic_name}?"
        ):
            chunks.append(chunk)
        logger.info("tutor_turn_done", response_chars=len("".join(chunks)))

        # 2. Geração de exercício adaptativo
        exercise = await generate_exercise(db, student, topic, "multipla_escolha")
        logger.info(
            "exercise_done",
            exercise_id=str(exercise.id),
            difficulty=exercise.difficulty,
            question_preview=exercise.content["question"][:80],
        )

    await engine.dispose()
    logger.info("agents_cycle_ok")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testa o ciclo completo dos agentes NERV")
    parser.add_argument("--student-email", default="aluno@demo.nerv.ai")
    parser.add_argument("--subject", default="Matemática")
    parser.add_argument("--topic", default="Funções quadráticas")
    args = parser.parse_args()
    asyncio.run(main(args.student_email, args.subject, args.topic))
