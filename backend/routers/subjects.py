"""Matérias e tópicos (catálogo BNCC) — leitura para qualquer usuário logado."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models import Subject, Topic, User

router = APIRouter(prefix="/subjects", tags=["subjects"])


class SubjectPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    bncc_code: str | None
    grade_range: str | None


class TopicPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    bncc_skill_code: str | None
    description: str | None
    difficulty_level: int | None


@router.get("", response_model=list[SubjectPublic])
async def list_subjects(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Subject]:
    result = await db.scalars(select(Subject).order_by(Subject.name))
    return list(result)


@router.get("/{subject_id}/topics", response_model=list[TopicPublic])
async def list_topics(
    subject_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Topic]:
    result = await db.scalars(
        select(Topic).where(Topic.subject_id == subject_id).order_by(Topic.name)
    )
    return list(result)
