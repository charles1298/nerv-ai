"""JWT, bcrypt e rate limiting (Redis).

O payload JWT segue a seção 9 do CLAUDE.md:
    sub, school_id, role, grade (apenas students), exp, type (access | refresh)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models import User

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user: User, token_type: str, expires_delta: timedelta) -> str:
    payload: dict[str, str | None | float] = {
        "sub": str(user.id),
        "school_id": str(user.school_id) if user.school_id else None,
        "role": user.role,
        "type": token_type,
        "exp": (datetime.now(timezone.utc) + expires_delta).timestamp(),
    }
    if user.role == "student":
        payload["grade"] = user.grade
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user: User) -> str:
    return _create_token(user, "access", timedelta(minutes=settings.jwt_access_token_expire_minutes))


def create_refresh_token(user: User) -> str:
    return _create_token(user, "refresh", timedelta(days=settings.jwt_refresh_token_expire_days))


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado") from e
    if payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tipo de token incorreto")
    return payload


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_token(token)
    user = await db.scalar(select(User).where(User.id == uuid.UUID(payload["sub"])))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado")
    return user


def require_role(*roles: str):
    """Dependency factory: restringe o endpoint aos papéis informados."""

    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão insuficiente")
        return user

    return checker


# --- Rate limiting (seção 9 do CLAUDE.md) ---

RATE_LIMITS: dict[str, tuple[int, int]] = {
    # nome: (máximo de requests, janela em segundos)
    "tutoring_messages": (30, 60),
    "exercise_generation": (20, 60),
    "image_uploads": (10, 60),
    "redacao_submission": (5, 3600),
}


def rate_limit(limit_name: str):
    """Dependency factory: rate limit por usuário via Redis (contador com TTL)."""
    max_requests, window_seconds = RATE_LIMITS[limit_name]

    async def checker(
        request: Request,
        user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        key = f"ratelimit:{limit_name}:{user.id}"
        try:
            redis = get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window_seconds)
            if current > max_requests:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    f"Limite de {max_requests} requisições por {window_seconds}s atingido. Tente novamente em instantes.",
                )
        except HTTPException:
            raise
        except Exception as e:  # Redis indisponível não pode derrubar a tutoria
            logger.warning("rate_limit_redis_unavailable", limit=limit_name, error=str(e), path=request.url.path)

    return checker
