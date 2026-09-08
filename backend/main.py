"""Entrypoint FastAPI do NERV AI.

Em desenvolvimento o schema é criado via create_all; em staging/produção use
Alembic (alembic upgrade head) — o lifespan não toca no schema fora de dev.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
from services import storage_service

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

# Sem R2, o storage grava em disco e storage_service.public_url() devolve
# {backend_url}/uploads/<key>. Sem este mount essa URL e 404 e a foto enviada
# pelo aluno nunca aparece — e o caminho padrao fora de serverless.
#
# Em serverless o filesystem e somente-leitura: o mkdir levantaria OSError
# durante o import e derrubaria a aplicacao inteira, nao so o upload.
if not storage_service.r2_enabled() and not os.getenv("VERCEL"):
    _upload_dir = Path(settings.local_upload_dir)
    try:
        _upload_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("local_uploads_indisponivel", path=str(_upload_dir), error=str(exc))
    else:
        app.mount(
            f"/{settings.local_upload_dir}",
            StaticFiles(directory=_upload_dir),
            name="uploads",
        )
        logger.info("local_uploads_servidos", path=str(_upload_dir))


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
