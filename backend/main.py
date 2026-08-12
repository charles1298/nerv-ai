"""Entrypoint FastAPI do NERV AI.

Em desenvolvimento o schema é criado via create_all; em staging/produção use
Alembic (alembic upgrade head) — o lifespan não toca no schema fora de dev.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from core.config import settings
from core.database import Base, engine
from routers import (
    auth,
    exercises,
    gamification,
    lgpd,
    redacoes,
    reports,
    sessions,
    students,
    subjects,
    upload,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "development":
        async with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("dev_schema_ready")
    yield
    await engine.dispose()


app = FastAPI(
    title="NERV AI",
    description="Sistema de Inteligência Educacional Adaptativa",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Sem isto o front (outra origem) não lê o nome do arquivo nos downloads de PDF.
    expose_headers=["Content-Disposition"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(sessions.router)
app.include_router(exercises.router)
app.include_router(upload.router)
app.include_router(redacoes.router)
app.include_router(gamification.router)
app.include_router(reports.router)
app.include_router(lgpd.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
