"""Schemas Pydantic de autenticação e usuários."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal["student", "teacher", "manager", "admin"]


class SchoolRegisterRequest(BaseModel):
    """Cadastro de escola + usuário admin inicial (fluxo da seção 9)."""

    school_name: str = Field(min_length=2, max_length=200)
    cnpj: str | None = Field(default=None, max_length=18)
    admin_name: str = Field(min_length=2, max_length=200)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)


class UserCreateRequest(BaseModel):
    """Admin/professor cria usuários dentro da própria escola."""

    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role
    grade: str | None = None  # obrigatório para students, validado no router


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    school_id: uuid.UUID | None
    name: str
    email: EmailStr
    role: str
    grade: str | None
    avatar_url: str | None
    created_at: datetime
