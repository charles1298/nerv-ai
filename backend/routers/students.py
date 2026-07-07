"""Gestão de usuários da escola — isolamento multi-tenant por school_id."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user, hash_password, require_role
from models import School, User
from schemas.auth import UserCreateRequest, UserPublic

logger = structlog.get_logger()
router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
) -> User:
    """Professor/gestor/admin cria usuários dentro da própria escola.

    Professores só podem criar alunos; gestores e admins criam qualquer papel.
    """
    if current.role == "teacher" and body.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Professores só podem criar alunos")
    if body.role == "student" and not body.grade:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Alunos precisam de série (grade)")

    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")

    if body.role == "student":
        school = await db.scalar(select(School).where(School.id == current.school_id))
        students_count = await db.scalar(
            select(func.count(User.id)).where(User.school_id == current.school_id, User.role == "student")
        )
        if school is not None and students_count >= school.max_students:
            raise HTTPException(
                status.HTTP_402_PAYMENT_REQUIRED,
                f"Limite de {school.max_students} alunos do plano '{school.plan}' atingido",
            )

    user = User(
        school_id=current.school_id,
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        grade=body.grade if body.role == "student" else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("user_created", user_id=str(user.id), role=user.role, created_by=str(current.id))
    return user


@router.get("", response_model=list[UserPublic])
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_role("teacher", "manager", "admin"))],
) -> list[User]:
    """Lista alunos da escola do usuário logado (nunca de outros tenants)."""
    result = await db.scalars(
        select(User)
        .where(User.school_id == current.school_id, User.role == "student")
        .order_by(User.name)
    )
    return list(result)


@router.get("/me", response_model=UserPublic)
async def get_me(current: Annotated[User, Depends(get_current_user)]) -> User:
    return current
