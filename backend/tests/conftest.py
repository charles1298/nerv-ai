"""Fixtures de teste — banco SQLite async isolado por teste, sem serviços externos."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.database import Base, get_db
from main import app


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    await client.post(
        "/auth/register-school",
        json={
            "school_name": "Escola Teste",
            "admin_name": "Admin Teste",
            "admin_email": "admin@teste.com",
            "admin_password": "senha-segura-123",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "admin@teste.com", "password": "senha-segura-123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def student_token(client: AsyncClient, admin_token: str) -> str:
    await client.post(
        "/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Aluno Teste",
            "email": "aluno@teste.com",
            "password": "senha-aluno-123",
            "role": "student",
            "grade": "9ano_ef",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "aluno@teste.com", "password": "senha-aluno-123"},
    )
    return resp.json()["access_token"]
