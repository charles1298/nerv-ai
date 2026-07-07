"""Testes das Fases 2/3 — redação, gamificação, upload, relatórios e LGPD.

Todas as chamadas ao modelo são mockadas; nenhum serviço externo é necessário.
"""

import io
import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

import agents.redacao_agent as redacao_agent
import agents.report_agent as report_agent
import agents.tutor_agent as tutor_agent
import routers.upload as upload_router_module
from schemas.redacao import RedacaoAvaliacao

pytestmark = pytest.mark.asyncio

AVALIACAO_VALIDA = {
    "nota_total": 760,
    "notas_por_criterio": {"C1": 160, "C2": 200, "C3": 160, "C4": 160, "C5": 80},
    "analise_detalhada": {
        "pontos_fortes": ["Bom repertório sociocultural"],
        "pontos_fracos": ["Proposta de intervenção incompleta"],
        "erros_gramaticais": [
            {"trecho": "menas pessoas", "erro": "concordância", "correcao": "menos pessoas"}
        ],
    },
    "reescrita_sugerida": "Diante disso, cabe ao Estado...",
    "nota_estimada_real_enem": "Entre 700 e 780",
    "proximos_passos": ["Praticar proposta de intervenção"],
}


# --- Schema de redação ---


async def test_redacao_avaliacao_valida():
    avaliacao = RedacaoAvaliacao.model_validate(AVALIACAO_VALIDA)
    assert avaliacao.nota_total == 760


async def test_redacao_rejeita_nota_fora_dos_niveis():
    broken = {
        **AVALIACAO_VALIDA,
        "notas_por_criterio": {"C1": 150, "C2": 200, "C3": 160, "C4": 160, "C5": 80},
    }
    with pytest.raises(ValidationError):
        RedacaoAvaliacao.model_validate(broken)


async def test_redacao_rejeita_criterio_faltando():
    broken = {**AVALIACAO_VALIDA, "notas_por_criterio": {"C1": 160, "C2": 200}}
    with pytest.raises(ValidationError):
        RedacaoAvaliacao.model_validate(broken)


# --- Fluxo de redação + gamificação via API ---


async def test_submit_essay_awards_xp(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return dict(AVALIACAO_VALIDA)

    monkeypatch.setattr(redacao_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/redacoes",
        headers=headers,
        json={"theme": "Desafios da educação digital no Brasil", "content": "x" * 300},
    )
    assert resp.status_code == 201
    assert resp.json()["nota_total"] == 760

    gam = await client.get("/gamification/me", headers=headers)
    body = gam.json()
    # redacao_submetida (40) + streak dia 1; sem badge de 800+
    assert body["xp_total"] >= 40
    assert body["streak_days"] == 1
    assert "escritor" not in [b["id"] for b in body["badges"]]


async def test_essay_800_plus_earns_badge(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    alta = {
        **AVALIACAO_VALIDA,
        "notas_por_criterio": {"C1": 200, "C2": 200, "C3": 160, "C4": 160, "C5": 120},
    }

    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return dict(alta)

    monkeypatch.setattr(redacao_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/redacoes",
        headers=headers,
        json={"theme": "Tema de teste para badge", "content": "y" * 300},
    )
    assert resp.status_code == 201
    assert resp.json()["nota_total"] == 840  # soma recalculada no agente

    gam = await client.get("/gamification/me", headers=headers)
    assert "escritor" in [b["id"] for b in gam.json()["badges"]]


# --- Upload multimodal ---


async def test_upload_image_analyzed(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch, tmp_path
):
    async def fake_analyze(image_base64, mime_type, student_prompt, student_context, student_id):
        return {"analysis": "É um exercício de frações. Vamos por partes: $\\frac{1}{2}$..."}

    monkeypatch.setattr(upload_router_module, "analyze_uploaded_image", fake_analyze)
    monkeypatch.setattr(
        "services.storage_service.settings.local_upload_dir", str(tmp_path)
    )

    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/upload",
        headers=headers,
        files={"file": ("prova.png", io.BytesIO(b"\x89PNG fake image"), "image/png")},
        data={"prompt": "Me ajuda com essa questão?"},
    )
    assert resp.status_code == 201
    assert "frações" in resp.json()["analysis"]


async def test_upload_rejects_wrong_mime(client: AsyncClient, student_token: str):
    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/upload",
        headers=headers,
        files={"file": ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert resp.status_code == 415


# --- Relatórios e isolamento multi-tenant ---


async def test_class_dashboard_requires_staff(client: AsyncClient, student_token: str):
    resp = await client.get(
        "/reports/turma", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 403


async def test_class_dashboard_lists_students(
    client: AsyncClient, admin_token: str, student_token: str
):
    resp = await client.get("/reports/turma", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Aluno Teste" in names


async def test_student_report_with_narrative(
    client: AsyncClient, admin_token: str, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return {
            "resumo": "Aluno em início de jornada.",
            "evolucao": "Sem dados suficientes ainda.",
            "pontos_fortes": [],
            "pontos_atencao": [],
            "recomendacoes": ["Incentivar primeira sessão de tutoria"],
            "proximos_topicos": [],
        }

    monkeypatch.setattr(report_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {admin_token}"}
    turma = await client.get("/reports/turma", headers=headers)
    student_id = turma.json()[0]["student_id"]

    resp = await client.get(f"/reports/aluno/{student_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["narrative"]["resumo"] == "Aluno em início de jornada."


async def test_student_report_other_school_404(client: AsyncClient, admin_token: str):
    resp = await client.get(
        f"/reports/aluno/{uuid.uuid4()}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 404


# --- Sessão com insights (end) ---


async def test_end_session_generates_insights(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_stream(system_prompt, messages, student_id, max_tokens=4096):
        yield "Vamos lá!"

    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return {"insights": ["Aluno demonstrou interesse em frações"], "quality_score": 0.9}

    monkeypatch.setattr(tutor_agent, "stream_tutor_response", fake_stream)
    monkeypatch.setattr(tutor_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {student_token}"}
    session = (await client.post("/sessions", headers=headers, json={})).json()

    async with client.stream(
        "POST", f"/sessions/{session['id']}/chat", headers=headers, json={"content": "oi"}
    ) as resp:
        async for _ in resp.aiter_text():
            continue

    end = await client.post(f"/sessions/{session['id']}/end", headers=headers)
    assert end.status_code == 200

    gam = await client.get("/gamification/me", headers=headers)
    body = gam.json()
    assert body["xp_total"] >= 50  # sessao_completada
    assert "primeira_sessao" in [b["id"] for b in body["badges"]]


# --- LGPD ---


async def test_lgpd_export_and_erasure(client: AsyncClient, student_token: str):
    headers = {"Authorization": f"Bearer {student_token}"}

    export = await client.get("/lgpd/export", headers=headers)
    assert export.status_code == 200
    assert export.json()["user"]["email"] == "aluno@teste.com"

    erase = await client.delete("/lgpd/me", headers=headers)
    assert erase.status_code == 204

    me = await client.get("/students/me", headers=headers)
    assert me.json()["name"] == "Usuário removido"
    assert "anonimizado" in me.json()["email"]
