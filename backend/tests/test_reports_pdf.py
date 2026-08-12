"""Exportação em PDF dos relatórios pedagógicos (Fase 3).

O modelo é sempre mockado; a geração do PDF em si é real (ReportLab).
"""

import uuid

import pytest
from httpx import AsyncClient

import agents.report_agent as report_agent
from core.config import settings
from services.pdf_service import school_overview_pdf, student_report_pdf

pytestmark = pytest.mark.asyncio

NARRATIVA = {
    "resumo": "Aluno com bom ritmo em álgebra.",
    "evolucao": "Evolução consistente nas últimas semanas.",
    "pontos_fortes": ["Persistência nas tentativas"],
    "pontos_atencao": ["Interpretação de enunciado"],
    "recomendacoes": ["Propor exercícios contextualizados"],
    "proximos_topicos": ["Funções quadráticas"],
}

AGREGADOS = {
    "sessions_count": 4,
    "last_session_at": "2026-08-01T14:30:00+00:00",
    "exercises_attempted": 20,
    "exercises_correct": 13,
    "correct_rate": 0.65,
    "avg_score": 6.8,
    "mastered_topics": ["Frações"],
    "struggling_topics": ["Equações do 2º grau"],
    "best_essay_score": 720,
}


def _assert_pdf(content: bytes) -> None:
    assert content.startswith(b"%PDF-"), "não é um PDF"
    assert b"%%EOF" in content[-1024:], "PDF sem marcador de fim"
    assert len(content) > 1000, "PDF suspeito de estar vazio"


async def _staff_token(client: AsyncClient, admin_token: str, role: str, email: str) -> str:
    """Cria um professor/gestor na escola do admin e devolve o token dele."""
    resp = await client.post(
        "/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": f"Staff {role}",
            "email": email,
            "password": "senha-staff-123",
            "role": role,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    login = await client.post(
        "/auth/login", json={"email": email, "password": "senha-staff-123"}
    )
    return login.json()["access_token"]


# --- Serviço de PDF (unitário) ---


async def test_student_pdf_escapes_markup_in_names_and_narrative():
    """Nome com acento e `&` não pode quebrar o mini-HTML do Paragraph."""
    student = {"id": str(uuid.uuid4()), "name": "Ana & João <Conceição>", "grade": "9ano_ef"}
    narrativa = {**NARRATIVA, "resumo": "Domina < e > além de & no texto."}
    _assert_pdf(student_report_pdf(student, AGREGADOS, "atencao", narrativa))


async def test_student_pdf_without_narrative_still_renders():
    student = {"id": str(uuid.uuid4()), "name": "Aluno Sem Narrativa", "grade": None}
    _assert_pdf(student_report_pdf(student, AGREGADOS, "critico", None))


async def test_student_pdf_handles_empty_aggregates():
    """Aluno recém-criado: tudo zerado/None não pode estourar formatação."""
    vazio = {
        "sessions_count": 0,
        "last_session_at": None,
        "exercises_attempted": 0,
        "exercises_correct": 0,
        "correct_rate": None,
        "avg_score": None,
        "mastered_topics": [],
        "struggling_topics": [],
        "best_essay_score": None,
    }
    student = {"id": str(uuid.uuid4()), "name": "Aluno Novo", "grade": "1ano_em"}
    _assert_pdf(student_report_pdf(student, vazio, "em_dia", None))


async def test_school_pdf_renders_heatmap_and_bncc():
    overview = {
        "students_count": 42,
        "active_students_last_7_days": 17,
        "heatmap": [
            {"grade": "9ano_ef", "subject": "Matemática", "attempts": 120, "correct_rate": 0.82},
            {"grade": "9ano_ef", "subject": "Português", "attempts": 90, "correct_rate": 0.55},
            {"grade": "1ano_em", "subject": "Física", "attempts": 40, "correct_rate": 0.31},
            {"grade": None, "subject": "Química", "attempts": 0, "correct_rate": None},
        ],
    }
    bncc = [
        {
            "subject": "Matemática",
            "bncc_code": "MT",
            "topics_total": 10,
            "topics_mastered": 4,
            "mastery_pct": 40.0,
        }
    ]
    _assert_pdf(school_overview_pdf("Escola Estadual São João", overview, bncc))


async def test_school_pdf_without_data():
    overview = {"students_count": 0, "active_students_last_7_days": 0, "heatmap": []}
    _assert_pdf(school_overview_pdf("Escola Vazia", overview, []))


# --- Endpoints ---


async def test_student_report_pdf_download(
    client: AsyncClient, admin_token: str, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return NARRATIVA

    monkeypatch.setattr(report_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {admin_token}"}
    turma = await client.get("/reports/turma", headers=headers)
    student_id = turma.json()[0]["student_id"]

    resp = await client.get(f"/reports/aluno/{student_id}/pdf", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment;" in resp.headers["content-disposition"]
    assert "relatorio-aluno-teste.pdf" in resp.headers["content-disposition"]
    _assert_pdf(resp.content)


async def test_student_report_pdf_survives_model_failure(
    client: AsyncClient, admin_token: str, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    """Se o modelo cair, o PDF ainda sai com os quantitativos do banco."""

    async def boom(system_prompt, user_prompt, student_id, max_tokens=2048):
        raise RuntimeError("modelo indisponível")

    monkeypatch.setattr(report_agent, "complete_json", boom)

    headers = {"Authorization": f"Bearer {admin_token}"}
    turma = await client.get("/reports/turma", headers=headers)
    student_id = turma.json()[0]["student_id"]

    resp = await client.get(f"/reports/aluno/{student_id}/pdf", headers=headers)
    assert resp.status_code == 200
    _assert_pdf(resp.content)


async def test_student_report_pdf_requires_staff(client: AsyncClient, student_token: str):
    resp = await client.get(
        f"/reports/aluno/{uuid.uuid4()}/pdf",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403


async def test_student_report_pdf_other_school_404(client: AsyncClient, admin_token: str):
    resp = await client.get(
        f"/reports/aluno/{uuid.uuid4()}/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


async def test_school_overview_pdf_download(client: AsyncClient, admin_token: str):
    resp = await client.get(
        "/reports/escola/pdf", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "visao-escola-escola-teste.pdf" in resp.headers["content-disposition"]
    _assert_pdf(resp.content)


async def test_pdf_download_exposes_filename_to_the_browser(
    client: AsyncClient, admin_token: str
):
    """Sem expor Content-Disposition no CORS, o front (outra origem) baixaria
    o arquivo com nome genérico. Regressão do ajuste em main.py."""
    resp = await client.get(
        "/reports/escola/pdf",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Origin": settings.frontend_url,
        },
    )
    assert resp.status_code == 200
    exposed = resp.headers.get("access-control-expose-headers", "")
    assert "Content-Disposition" in exposed


async def test_school_overview_pdf_denied_to_teacher(client: AsyncClient, admin_token: str):
    """Visão da escola é do gestor: professor não baixa (seção 7.3)."""
    teacher_token = await _staff_token(client, admin_token, "teacher", "prof@teste.com")
    resp = await client.get(
        "/reports/escola/pdf", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code == 403
