"""Configuração sensível ao ambiente de hospedagem."""

import pytest
from sqlalchemy.pool import NullPool

from core.config import Settings
from core.database import _pool_kwargs

pytestmark = pytest.mark.asyncio


async def test_postgres_url_gets_async_driver():
    """Railway/Render injetam `postgresql://`, que o SQLAlchemy async rejeita."""
    s = Settings(database_url="postgresql://u:p@host:5432/nerv")
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/nerv"


async def test_legacy_postgres_scheme_also_normalized():
    """Heroku ainda emite o esquema antigo `postgres://`."""
    s = Settings(database_url="postgres://u:p@host:5432/nerv")
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/nerv"


async def test_explicit_driver_is_preserved():
    s = Settings(database_url="postgresql+asyncpg://u:p@host:5432/nerv")
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/nerv"


async def test_sqlite_url_untouched():
    """O SQLite de dev/teste nao pode ser reescrito."""
    s = Settings(database_url="sqlite+aiosqlite:///./nerv_ai.db")
    assert s.database_url == "sqlite+aiosqlite:///./nerv_ai.db"


async def test_password_with_special_chars_survives():
    """Senha gerada pela hospedagem costuma ter `/` e `@` — o prefixo trocado
    nao pode comer o resto da URL."""
    s = Settings(database_url="postgresql://u:a/b@c@host:5432/nerv")
    assert s.database_url == "postgresql+asyncpg://u:a/b@c@host:5432/nerv"


async def test_sslmode_stripped_for_asyncpg():
    """Neon entrega `?sslmode=require`, que o asyncpg nao aceita."""
    s = Settings(database_url="postgresql://u:p@ep-x.neon.tech/nerv?sslmode=require")
    assert s.database_url == "postgresql+asyncpg://u:p@ep-x.neon.tech/nerv"


async def test_channel_binding_stripped_but_other_params_kept():
    s = Settings(
        database_url=(
            "postgresql://u:p@ep-x.neon.tech/nerv"
            "?sslmode=require&channel_binding=require&application_name=nerv"
        )
    )
    assert s.database_url == (
        "postgresql+asyncpg://u:p@ep-x.neon.tech/nerv?application_name=nerv"
    )


async def test_sqlite_query_string_untouched():
    """A limpeza e' so do Postgres — nao pode mexer em outros dialetos."""
    s = Settings(database_url="sqlite+aiosqlite:///./x.db?cache=shared")
    assert s.database_url == "sqlite+aiosqlite:///./x.db?cache=shared"


# --- Pool de conexões por ambiente ---


async def test_no_app_side_pool_on_serverless(monkeypatch: pytest.MonkeyPatch):
    """Na Vercel, pool na aplicação esgotaria as conexões do Postgres."""
    monkeypatch.setenv("VERCEL", "1")
    assert _pool_kwargs() == {"poolclass": NullPool}


async def test_pool_kept_outside_serverless(monkeypatch: pytest.MonkeyPatch):
    """Local e em container o pool do SQLAlchemy e' desejavel."""
    monkeypatch.delenv("VERCEL", raising=False)
    assert _pool_kwargs() == {}
