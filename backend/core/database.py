"""Engine SQLAlchemy async e sessão por request."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings


class Base(DeclarativeBase):
    pass


def _pool_kwargs() -> dict:
    """Sem pool na aplicação quando rodando serverless.

    Em serverless cada instância da função mantém seu próprio pool (5 + 10 de
    overflow por padrão), e dezenas de instâncias concorrentes esgotariam o
    limite de conexões de um Postgres gratuito. O correto é abrir e fechar por
    request e deixar o pooling para o provedor (pgBouncer do Neon/Supabase).
    A Vercel define VERCEL=1 no ambiente automaticamente.
    """
    if os.getenv("VERCEL"):
        return {"poolclass": NullPool}
    return {}


engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    **_pool_kwargs(),
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI: uma sessão de banco por request."""
    async with async_session_maker() as session:
        yield session
