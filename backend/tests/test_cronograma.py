"""Cronograma de estudos personalizado — schema, orçamento de tempo e endpoints.

O modelo é mockado: o que se testa é o contrato entre o que ele devolve e o que
o aluno recebe, incluindo a proteção que impede um plano de estourar o tempo que
o aluno disse ter.
"""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from agents import cronograma_agent
from schemas.cronograma import CronogramaGerado, DiaEstudo

pytestmark = pytest.mark.asyncio


def _plano(minutos_por_bloco: int = 30, blocos_por_dia: int = 1) -> dict:
    return {
        "resumo": "Plano para destravar porcentagem em duas semanas.",
        "estrategia": "Começa pelo que você errou mais e revisa o resto no fim.",
        "semanas": [
            {
                "numero": 1,
                "foco": "Retomar porcentagem",
                "dias": [
                    {
                        "dia": "Segunda",
                        "blocos": [
                            {
                                "materia": "Matemática",
                                "topico": "Porcentagem",
                                "minutos": minutos_por_bloco,
                                "atividade": "exercicios",
                                "descricao": "Resolver 5 questões de nível 2.",
                            }
                            for _ in range(blocos_por_dia)
                        ],
                    }
                ],
            }
        ],
        "dicas": ["Estude sempre no mesmo horário."],
    }


# --- schema ---


async def test_plano_valido_e_aceito():
    plano = CronogramaGerado.model_validate(_plano())
    assert plano.semanas[0].dias[0].minutos_totais == 30


async def test_atividade_fora_da_lista_e_rejeitada():
    """Lista fechada: com texto livre a interface não consegue dar ícone ao bloco."""
    bruto = _plano()
    bruto["semanas"][0]["dias"][0]["blocos"][0]["atividade"] = "meditar"
    with pytest.raises(ValidationError):
        CronogramaGerado.model_validate(bruto)


async def test_dia_da_semana_e_normalizado():
    """O modelo alterna entre 'Segunda' e 'Segunda-feira' na mesma resposta."""
    dia = DiaEstudo.model_validate(
        {
            "dia": "segunda-feira",
            "blocos": [
                {
                    "materia": "Matemática",
                    "topico": "Frações",
                    "minutos": 20,
                    "atividade": "revisao",
                    "descricao": "Revisar a tabela de equivalências.",
                }
            ],
        }
    )
    assert dia.dia == "Segunda"


async def test_dia_inexistente_e_rejeitado():
    bruto = _plano()
    bruto["semanas"][0]["dias"][0]["dia"] = "Octoday"
    with pytest.raises(ValidationError):
        CronogramaGerado.model_validate(bruto)


async def test_dia_sem_blocos_e_rejeitado():
    bruto = _plano()
    bruto["semanas"][0]["dias"][0]["blocos"] = []
    with pytest.raises(ValidationError):
        CronogramaGerado.model_validate(bruto)


# --- orçamento de tempo ---


async def test_plano_dentro_do_orcamento_nao_acusa():
    plano = CronogramaGerado.model_validate(_plano(minutos_por_bloco=30))
    assert plano.dias_acima_do_orcamento(30) == []


async def test_tolerancia_absorve_excesso_pequeno():
    """35 min num orçamento de 30 não invalida o dia — 20% de folga."""
    plano = CronogramaGerado.model_validate(_plano(minutos_por_bloco=35))
    assert plano.dias_acima_do_orcamento(30) == []


async def test_plano_que_estoura_o_tempo_e_detectado():
    """Três blocos de 60 min para quem tem 30: o erro que faz o aluno desistir."""
    plano = CronogramaGerado.model_validate(_plano(minutos_por_bloco=60, blocos_por_dia=3))
    estourados = plano.dias_acima_do_orcamento(30)
    assert len(estourados) == 1
    assert "180 min" in estourados[0]


# --- endpoints ---


async def test_gera_e_lista_cronograma(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        # O prompt precisa carregar as restrições do aluno, senão o plano não é dele.
        assert "30 minutos" in user_prompt
        assert "prova de matemática" in user_prompt.lower()
        return _plano()

    monkeypatch.setattr(cronograma_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/cronogramas",
        headers=headers,
        json={
            "objetivo": "Passar na prova de matemática",
            "semanas": 1,
            "dias_por_semana": 1,
            "minutos_por_dia": 30,
            "materias": ["Matemática"],
        },
    )
    assert resp.status_code == 201
    criado = resp.json()
    assert criado["semanas"][0]["dias"][0]["blocos"][0]["materia"] == "Matemática"
    assert criado["minutos_por_dia"] == 30

    listagem = await client.get("/cronogramas", headers=headers)
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1
    # A listagem é enxuta de propósito: carregar semanas inteiras por item pesaria.
    assert "semanas" not in listagem.json()[0]

    detalhe = await client.get(f"/cronogramas/{criado['id']}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["resumo"] == criado["resumo"]


async def test_retenta_quando_o_plano_estoura_o_tempo(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    """Primeira resposta estoura o orçamento; a segunda respeita e é a que vale."""
    chamadas: list[str] = []

    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        chamadas.append(user_prompt)
        if len(chamadas) == 1:
            return _plano(minutos_por_bloco=60, blocos_por_dia=3)
        return _plano(minutos_por_bloco=30)

    monkeypatch.setattr(cronograma_agent, "complete_json", fake_complete_json)

    resp = await client.post(
        "/cronogramas",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "objetivo": "Recuperar a média",
            "semanas": 1,
            "dias_por_semana": 1,
            "minutos_por_dia": 30,
        },
    )
    assert resp.status_code == 201
    assert len(chamadas) == 2
    # A segunda chamada tem que dizer QUAIS dias estouraram — instrução genérica
    # o modelo já ignorou na primeira.
    assert "ATENÇÃO" in chamadas[1]
    assert "180 min" in chamadas[1]
    assert resp.json()["semanas"][0]["dias"][0]["blocos"][0]["minutos"] == 30


async def test_modelo_invalido_vira_502(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return {"resumo": "sem as demais chaves"}

    monkeypatch.setattr(cronograma_agent, "complete_json", fake_complete_json)

    resp = await client.post(
        "/cronogramas",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "objetivo": "Estudar para o ENEM",
            "semanas": 2,
            "dias_por_semana": 3,
            "minutos_por_dia": 60,
        },
    )
    assert resp.status_code == 502
    assert "cronograma" in resp.json()["detail"].lower()


async def test_cronograma_de_outro_aluno_nao_e_acessivel(
    client: AsyncClient, student_token: str, admin_token: str, monkeypatch: pytest.MonkeyPatch
):
    """Isolamento: o filtro por student_id vai na query, não numa checagem depois."""

    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return _plano()

    monkeypatch.setattr(cronograma_agent, "complete_json", fake_complete_json)

    criado = await client.post(
        "/cronogramas",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "objetivo": "Melhorar em frações",
            "semanas": 1,
            "dias_por_semana": 1,
            "minutos_por_dia": 30,
        },
    )
    plano_id = criado.json()["id"]

    outro = await client.post(
        "/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Outro Aluno",
            "email": "outro.aluno@teste.com",
            "password": "senha-outro-123",
            "role": "student",
            "grade": "9ano_ef",
        },
    )
    assert outro.status_code in (200, 201)
    login = await client.post(
        "/auth/login",
        json={"email": "outro.aluno@teste.com", "password": "senha-outro-123"},
    )
    token_outro = login.json()["access_token"]

    resp = await client.get(
        f"/cronogramas/{plano_id}", headers={"Authorization": f"Bearer {token_outro}"}
    )
    assert resp.status_code == 404


async def test_formulario_rejeita_valores_impossiveis(client: AsyncClient, student_token: str):
    """13 semanas ou 8 dias por semana não existem — barrar antes de gastar o modelo."""
    headers = {"Authorization": f"Bearer {student_token}"}
    for corpo in (
        {"objetivo": "Estudar", "semanas": 13, "dias_por_semana": 3, "minutos_por_dia": 60},
        {"objetivo": "Estudar", "semanas": 2, "dias_por_semana": 8, "minutos_por_dia": 60},
        {"objetivo": "Estudar", "semanas": 2, "dias_por_semana": 3, "minutos_por_dia": 5},
    ):
        resp = await client.post("/cronogramas", headers=headers, json=corpo)
        assert resp.status_code == 422
