"""Normalização da DATABASE_URL vinda da hospedagem."""

import pytest

from core.config import Settings

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
