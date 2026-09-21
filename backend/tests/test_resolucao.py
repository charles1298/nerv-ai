"""Resolução de exercícios com explicação — schema, texto, foto e isolamento.

O modelo é mockado. O que se testa é o contrato entre o que ele devolve e o que
o aluno recebe, incluindo a renumeração dos passos e a honestidade sobre a
leitura do enunciado na foto.
"""

import json

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from agents import resolucao_agent
from schemas.resolucao import ResolucaoGerada

pytestmark = pytest.mark.asyncio

# PNG 1x1 válido — o endpoint checa o mime e o tamanho, não o conteúdo.
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _resolucao(passos: list[dict] | None = None, confianca: str = "alta") -> dict:
    return {
        "enunciado_interpretado": "Calcular a hipotenusa de um triângulo de catetos 3 e 4.",
        "materia": "Matemática",
        "topico": "Teorema de Pitágoras",
        # `is None` e nao `or`: lista vazia e' falsy e cairia no padrao,
        # fazendo o teste de "sem passos" testar a lista cheia.
        "passos": passos
        if passos is not None
        else [
            {
                "numero": 1,
                "titulo": "Identificar o que a questão pede",
                "explicacao": "Os catetos são conhecidos e falta a hipotenusa.",
                "expressao": None,
            },
            {
                "numero": 2,
                "titulo": "Aplicar o teorema",
                "explicacao": "A soma dos quadrados dos catetos é o quadrado da hipotenusa.",
                "expressao": "$a^2 = 3^2 + 4^2$",
            },
        ],
        "resposta_final": "A hipotenusa mede 5.",
        "conceito": "Em todo triângulo retângulo vale a relação de Pitágoras.",
        "erros_comuns": ["Somar os catetos em vez de somar os quadrados."],
        "como_conferir": "Eleve 5 ao quadrado: 25, que é 9 mais 16.",
        "exercicio_parecido": "Catetos 6 e 8: qual a hipotenusa?",
        "confianca": confianca,
    }


# --- schema ---


async def test_resolucao_valida():
    r = ResolucaoGerada.model_validate(_resolucao())
    assert r.resposta_final.startswith("A hipotenusa")
    assert r.passos[1].expressao == "$a^2 = 3^2 + 4^2$"


async def test_passos_fora_de_ordem_sao_renumerados():
    """O modelo devolve a lista trocada; a tela mostra o número em destaque."""
    bruto = _resolucao(
        passos=[
            {"numero": 5, "titulo": "Concluir", "explicacao": "Fim.", "expressao": None},
            {"numero": 2, "titulo": "Começar", "explicacao": "Início.", "expressao": None},
        ]
    )
    ordenados = ResolucaoGerada.model_validate(bruto).passos_ordenados()
    assert [p.numero for p in ordenados] == [1, 2]
    assert ordenados[0].titulo == "Começar"
    assert ordenados[1].titulo == "Concluir"


async def test_resolucao_sem_passos_e_rejeitada():
    bruto = _resolucao(passos=[])
    with pytest.raises(ValidationError):
        ResolucaoGerada.model_validate(bruto)


async def test_confianca_fora_da_lista_e_rejeitada():
    with pytest.raises(ValidationError):
        ResolucaoGerada.model_validate(_resolucao(confianca="mais ou menos"))


async def test_expressao_opcional():
    """Passo de interpretação de texto não tem conta nenhuma."""
    r = ResolucaoGerada.model_validate(_resolucao())
    assert r.passos[0].expressao is None


# --- resolução por texto ---


async def test_resolve_exercicio_digitado(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        # O enunciado e a dúvida do aluno precisam chegar ao modelo.
        assert "catetos 3 e 4" in user_prompt
        assert "não sei qual fórmula usar" in user_prompt
        return _resolucao()

    monkeypatch.setattr(resolucao_agent, "complete_json", fake_complete_json)

    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        "/resolucoes",
        headers=headers,
        json={
            "enunciado": "Um triângulo retângulo tem catetos 3 e 4. Qual a hipotenusa?",
            "duvida": "não sei qual fórmula usar",
        },
    )
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["origem"] == "texto"
    assert corpo["resposta_final"] == "A hipotenusa mede 5."
    assert corpo["imagem_url"] is None
    assert [p["numero"] for p in corpo["passos"]] == [1, 2]

    listagem = await client.get("/resolucoes", headers=headers)
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1
    # A listagem é enxuta: carregar passos e textos longos por item pesaria.
    assert "passos" not in listagem.json()[0]

    detalhe = await client.get(f"/resolucoes/{corpo['id']}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["conceito"].startswith("Em todo triângulo")


async def test_enunciado_curto_demais_e_barrado(client: AsyncClient, student_token: str):
    """Barra antes de gastar chamada de modelo com 'me ajuda'."""
    resp = await client.post(
        "/resolucoes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"enunciado": "me ajuda"},
    )
    assert resp.status_code == 422


async def test_modelo_invalido_vira_502(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return {"resposta_final": "42"}  # faltam todas as demais chaves

    monkeypatch.setattr(resolucao_agent, "complete_json", fake_complete_json)

    resp = await client.post(
        "/resolucoes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"enunciado": "Quanto é dois mais dois, explicando o raciocínio?"},
    )
    assert resp.status_code == 502
    assert "resolver" in resp.json()["detail"].lower()


# --- resolução por foto ---


async def test_resolve_exercicio_fotografado(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_analyze_image(image_base64, mime_type, prompt, student_id, max_tokens=2048):
        assert mime_type == "image/png"
        assert image_base64  # a imagem chega ao modelo
        # Modelo devolvendo JSON cercado é o caso comum fora da Anthropic.
        return "```json\n" + json.dumps(_resolucao()) + "\n```"

    monkeypatch.setattr(resolucao_agent, "analyze_image", fake_analyze_image)

    resp = await client.post(
        "/resolucoes/foto",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("exercicio.png", PNG_1X1, "image/png")},
        data={"duvida": "travei no segundo passo"},
    )
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["origem"] == "foto"
    # A foto fica guardada: se a resolução sair errada, é ela que explica o porquê.
    assert corpo["imagem_url"]
    assert corpo["enunciado"] == ""
    assert corpo["enunciado_interpretado"].startswith("Calcular a hipotenusa")


async def test_foto_ilegivel_devolve_confianca_baixa(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    """Não pode chutar: o aluno precisa saber que a leitura ficou duvidosa."""

    async def fake_analyze_image(image_base64, mime_type, prompt, student_id, max_tokens=2048):
        return json.dumps(_resolucao(confianca="baixa"))

    monkeypatch.setattr(resolucao_agent, "analyze_image", fake_analyze_image)

    resp = await client.post(
        "/resolucoes/foto",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("borrada.png", PNG_1X1, "image/png")},
    )
    assert resp.status_code == 201
    assert resp.json()["confianca"] == "baixa"


async def test_formato_de_arquivo_invalido(client: AsyncClient, student_token: str):
    resp = await client.post(
        "/resolucoes/foto",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("lista.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert resp.status_code == 415


async def test_arquivo_vazio(client: AsyncClient, student_token: str):
    resp = await client.post(
        "/resolucoes/foto",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("vazio.png", b"", "image/png")},
    )
    assert resp.status_code == 422


# --- isolamento ---


async def test_resolucao_de_outro_aluno_nao_e_acessivel(
    client: AsyncClient, student_token: str, admin_token: str, monkeypatch: pytest.MonkeyPatch
):
    async def fake_complete_json(system_prompt, user_prompt, student_id, max_tokens=2048):
        return _resolucao()

    monkeypatch.setattr(resolucao_agent, "complete_json", fake_complete_json)

    criado = await client.post(
        "/resolucoes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"enunciado": "Um triângulo retângulo tem catetos 3 e 4. Qual a hipotenusa?"},
    )
    resolucao_id = criado.json()["id"]

    outro = await client.post(
        "/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Outro Aluno",
            "email": "outro.resolucao@teste.com",
            "password": "senha-outro-123",
            "role": "student",
            "grade": "9ano_ef",
        },
    )
    assert outro.status_code in (200, 201)
    login = await client.post(
        "/auth/login",
        json={"email": "outro.resolucao@teste.com", "password": "senha-outro-123"},
    )
    token_outro = login.json()["access_token"]

    resp = await client.get(
        f"/resolucoes/{resolucao_id}", headers={"Authorization": f"Bearer {token_outro}"}
    )
    assert resp.status_code == 404

    # E a listagem dele não enxerga nada.
    listagem = await client.get(
        "/resolucoes", headers={"Authorization": f"Bearer {token_outro}"}
    )
    assert listagem.json() == []
