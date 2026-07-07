"""Auth: cadastro de escola, login e refresh (seção 9 do CLAUDE.md)."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models import School, User
from schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SchoolRegisterRequest,
    TokenResponse,
    UserPublic,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-school", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_school(
    body: SchoolRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Cadastra a escola (tenant) e seu admin inicial."""
    existing = await db.scalar(select(User).where(User.email == body.admin_email))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")

    school = School(name=body.school_name, cnpj=body.cnpj)
    db.add(school)
    await db.flush()

    admin = User(
        school_id=school.id,
        name=body.admin_name,
        email=body.admin_email,
        password_hash=hash_password(body.admin_password),
        role="admin",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    logger.info("school_registered", school_id=str(school.id))
    return admin


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    logger.info("user_login", user_id=str(user.id), role=user.role)
    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user = await db.scalar(select(User).where(User.id == uuid.UUID(payload["sub"])))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado")
    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )
