"""Testes do fluxo de autenticação e multi-tenancy básico."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_school_creates_admin(client: AsyncClient):
    resp = await client.post(
        "/auth/register-school",
        json={
            "school_name": "Escola Nova",
            "admin_name": "Diretora Ana",
            "admin_email": "ana@escola.com",
            "admin_password": "senha-forte-123",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "admin"
    assert body["school_id"] is not None


async def test_login_wrong_password_rejected(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/auth/login",
        json={"email": "admin@teste.com", "password": "senha-errada"},
    )
    assert resp.status_code == 401


async def test_duplicate_email_rejected(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/auth/register-school",
        json={
            "school_name": "Outra Escola",
            "admin_name": "Outro Admin",
            "admin_email": "admin@teste.com",
            "admin_password": "senha-forte-123",
        },
    )
    assert resp.status_code == 409


async def test_refresh_token_flow(client: AsyncClient, admin_token: str):
    login = await client.post(
        "/auth/login",
        json={"email": "admin@teste.com", "password": "senha-segura-123"},
    )
    refresh_token = login.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_access_token_cannot_be_used_as_refresh(client: AsyncClient, admin_token: str):
    resp = await client.post("/auth/refresh", json={"refresh_token": admin_token})
    assert resp.status_code == 401


async def test_student_cannot_create_users(client: AsyncClient, student_token: str):
    resp = await client.post(
        "/students",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "name": "Hacker",
            "email": "hacker@teste.com",
            "password": "senha-qualquer-1",
            "role": "admin",
        },
    )
    assert resp.status_code == 403


async def test_student_requires_grade(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Aluno Sem Série",
            "email": "semserie@teste.com",
            "password": "senha-qualquer-1",
            "role": "student",
        },
    )
    assert resp.status_code == 422


async def test_me_endpoint(client: AsyncClient, student_token: str):
    resp = await client.get("/students/me", headers={"Authorization": f"Bearer {student_token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "student"
    assert resp.json()["grade"] == "9ano_ef"
