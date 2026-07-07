"""Models ORM do NERV AI — schema completo da seção 4 do CLAUDE.md.

Desvios documentados do SQL de referência:
- mastered_topics/struggling_topics usam JSON (lista) em vez de TEXT[] para
  portabilidade entre Postgres e SQLite (testes).
- knowledge_chunks.embedding usa pgvector no Postgres e JSON no SQLite (o RAG
  só opera de fato em Postgres; em testes a busca degrada para vazio).
"""

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from core.database import Base

# JSONB no Postgres, JSON genérico em outros dialetos (testes com sqlite)
JsonColumn = JSONB().with_variant(JSON(), "sqlite")


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")  # free | basic | pro | enterprise
    max_students: Mapped[int] = mapped_column(Integer, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="school")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("schools.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))  # student | teacher | manager | admin
    grade: Mapped[str | None] = mapped_column(String(20))  # 1ano_ef | ... | 3ano_em
    avatar_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    school: Mapped[School | None] = relationship(back_populates="users")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    bncc_code: Mapped[str | None] = mapped_column(String(20))  # MT, LP, CN, CH
    grade_range: Mapped[str | None] = mapped_column(String(20))  # EF1, EF2, EM


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (CheckConstraint("difficulty_level BETWEEN 1 AND 5"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(200))
    bncc_skill_code: Mapped[str | None] = mapped_column(String(30))  # Ex: EF09MA07
    description: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[int | None] = mapped_column(Integer)

    subject: Mapped[Subject] = relationship()


class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id"))
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("topics.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float | None] = mapped_column(Float)
    insights: Mapped[list] = mapped_column(JsonColumn, default=list)

    student: Mapped[User] = relationship()
    subject: Mapped[Subject | None] = relationship()
    topic: Mapped[Topic | None] = relationship()
    messages: Mapped[list["SessionMessage"]] = relationship(
        back_populates="session", order_by="SessionMessage.created_at"
    )


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutoring_sessions.id"))
    role: Mapped[str] = mapped_column(String(10))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(20), default="text")  # text | image | math | code
    image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[TutoringSession] = relationship(back_populates="messages")


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (CheckConstraint("difficulty BETWEEN 1 AND 5"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("topics.id"))
    content: Mapped[dict] = mapped_column(JsonColumn)
    difficulty: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str | None] = mapped_column(String(30))  # multipla_escolha | dissertativa | redacao | calculo
    source: Mapped[str] = mapped_column(String(20), default="ai")  # ai | enem | vestibular
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic: Mapped[Topic | None] = relationship()
    attempts: Mapped[list["ExerciseAttempt"]] = relationship(back_populates="exercise")


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercises.id"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Float)  # 0.0 - 10.0
    feedback: Mapped[str | None] = mapped_column(Text)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    exercise: Mapped[Exercise] = relationship(back_populates="attempts")


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tutoring_sessions.id"))
    filename: Mapped[str] = mapped_column(Text)
    r2_key: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(50))
    analysis_result: Mapped[dict | None] = mapped_column(JsonColumn)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Essay(Base):
    """Redações submetidas e avaliadas no modelo ENEM (redacao_agent, seção 5.3)."""

    __tablename__ = "essays"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    theme: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    nota_total: Mapped[int | None] = mapped_column(Integer)  # 0-1000
    notas_por_criterio: Mapped[dict | None] = mapped_column(JsonColumn)  # {C1..C5: 0-200}
    analise_detalhada: Mapped[dict | None] = mapped_column(JsonColumn)
    reescrita_sugerida: Mapped[str | None] = mapped_column(Text)
    nota_estimada_real_enem: Mapped[str | None] = mapped_column(String(50))
    proximos_passos: Mapped[list | None] = mapped_column(JsonColumn)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StudentGamification(Base):
    """XP, streak e badges por aluno (seção 8 do CLAUDE.md)."""

    __tablename__ = "student_gamification"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[date | None] = mapped_column(Date)
    badges: Mapped[list] = mapped_column(JsonColumn, default=list)  # ids de BADGES


class StudentPerformance(Base):
    """Desempenho agregado por aluno/matéria/dia (atualizado a cada evento)."""

    __tablename__ = "student_performance"
    __table_args__ = (UniqueConstraint("student_id", "subject_id", "period_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id"))
    period_date: Mapped[date] = mapped_column(Date)
    sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    exercises_attempted: Mapped[int] = mapped_column(Integer, default=0)
    exercises_correct: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float | None] = mapped_column(Float)
    mastered_topics: Mapped[list] = mapped_column(JsonColumn, default=list)
    struggling_topics: Mapped[list] = mapped_column(JsonColumn, default=list)


class KnowledgeChunk(Base):
    """Corpus BNCC/ENEM para RAG (pgvector; JSON em SQLite só para testes)."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id"))
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("topics.id"))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))  # bncc | enem | livro_didatico
    embedding = mapped_column(Vector(1536).with_variant(JSON(), "sqlite"))
    meta: Mapped[dict] = mapped_column("metadata", JsonColumn, default=dict)
