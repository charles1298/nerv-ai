"""Seed de desenvolvimento: escola demo, usuários e catálogo inicial de matérias/tópicos.

Uso (a partir de backend/, com o venv ativo e o banco de pé):
    python ../scripts/seed_dev.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import structlog
from sqlalchemy import select

from core.database import Base, async_session_maker, engine
from core.security import hash_password
from models import School, Subject, Topic, User

logger = structlog.get_logger()

SUBJECTS = [
    {
        "name": "Matemática",
        "bncc_code": "MT",
        "grade_range": "EF2",
        "topics": [
            ("Funções quadráticas", "EF09MA06", 4),
            ("Equações de 1º grau", "EF07MA18", 2),
            ("Porcentagem e juros simples", "EF09MA05", 3),
            ("Teorema de Pitágoras", "EF09MA13", 3),
        ],
    },
    {
        "name": "Língua Portuguesa",
        "bncc_code": "LP",
        "grade_range": "EF2",
        "topics": [
            ("Interpretação de texto", "EF89LP33", 2),
            ("Figuras de linguagem", "EF89LP37", 3),
            ("Concordância verbal", "EF09LP06", 3),
        ],
    },
    {
        "name": "Ciências",
        "bncc_code": "CN",
        "grade_range": "EF2",
        "topics": [
            ("Sistema solar", "EF09CI14", 2),
            ("Cadeias alimentares", "EF06CI04", 2),
            ("Estados físicos da matéria", "EF06CI01", 1),
        ],
    },
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        existing = await db.scalar(select(School).where(School.name == "Escola Demo NERV"))
        if existing is not None:
            logger.info("seed_skipped", reason="Escola Demo NERV já existe")
            return

        school = School(name="Escola Demo NERV", plan="pro", max_students=500)
        db.add(school)
        await db.flush()

        db.add_all(
            [
                User(
                    school_id=school.id,
                    name="Admin Demo",
                    email="admin@demo.nerv.ai",
                    password_hash=hash_password("admin-demo-123"),
                    role="admin",
                ),
                User(
                    school_id=school.id,
                    name="Prof. Carla Souza",
                    email="professora@demo.nerv.ai",
                    password_hash=hash_password("prof-demo-123"),
                    role="teacher",
                ),
                User(
                    school_id=school.id,
                    name="João Pereira",
                    email="aluno@demo.nerv.ai",
                    password_hash=hash_password("aluno-demo-123"),
                    role="student",
                    grade="9ano_ef",
                ),
            ]
        )

        for subject_data in SUBJECTS:
            subject = Subject(
                name=subject_data["name"],
                bncc_code=subject_data["bncc_code"],
                grade_range=subject_data["grade_range"],
            )
            db.add(subject)
            await db.flush()
            for topic_name, bncc_skill, difficulty in subject_data["topics"]:
                db.add(
                    Topic(
                        subject_id=subject.id,
                        name=topic_name,
                        bncc_skill_code=bncc_skill,
                        difficulty_level=difficulty,
                    )
                )

        await db.commit()
        logger.info(
            "seed_completed",
            school="Escola Demo NERV",
            users=3,
            subjects=len(SUBJECTS),
            login_aluno="aluno@demo.nerv.ai / aluno-demo-123",
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
