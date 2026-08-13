"""Wrapper do provedor de IA — extração de JSON e ausência de chave.

As chamadas de rede não são exercitadas aqui; o que se testa é a tolerância ao
formato da resposta, que é onde modelos menores costumam divergir.
"""

import pytest

from services.ai_service import AINotConfigured, _client, extract_json, _with_system

pytestmark = pytest.mark.asyncio


# --- extract_json ---


async def test_json_puro():
    assert extract_json('{"nota": 760}') == {"nota": 760}


async def test_json_dentro_de_cerca_de_codigo():
    """Caso mais comum fora da Anthropic: ```json ... ```"""
    raw = '```json\n{"resumo": "Aluno em evolução"}\n```'
    assert extract_json(raw) == {"resumo": "Aluno em evolução"}


async def test_json_em_cerca_sem_linguagem():
    assert extract_json('```\n{"ok": true}\n```') == {"ok": True}


async def test_json_com_prosa_em_volta():
    """Modelo educado que explica antes de responder."""
    raw = 'Claro! Aqui está o resultado:\n{"C1": 160, "C2": 200}\nEspero ter ajudado.'
    assert extract_json(raw) == {"C1": 160, "C2": 200}


async def test_json_aninhado_pega_o_objeto_inteiro():
    """A busca vai da primeira `{` até a ultima `}` — nao pode truncar no meio."""
    raw = 'texto {"a": {"b": [1, 2]}, "c": "fim"} mais texto'
    assert extract_json(raw) == {"a": {"b": [1, 2]}, "c": "fim"}


async def test_acentuacao_preservada():
    raw = '{"texto": "progressão argumentativa e coesão"}'
    assert extract_json(raw)["texto"] == "progressão argumentativa e coesão"


async def test_lista_no_topo_e_rejeitada():
    """Os agentes esperam objeto; uma lista no topo nao serve."""
    with pytest.raises(ValueError):
        extract_json("[1, 2, 3]")


async def test_texto_sem_json_levanta():
    with pytest.raises(ValueError):
        extract_json("Desculpe, nao consegui responder.")


async def test_json_incompleto_levanta():
    with pytest.raises(ValueError):
        extract_json('{"nota": ')


# --- system prompt no protocolo da OpenAI ---


async def test_system_prompt_vira_primeira_mensagem():
    msgs = _with_system("Você é o NERV", [{"role": "user", "content": "oi"}])
    assert msgs[0] == {"role": "system", "content": "Você é o NERV"}
    assert msgs[1]["content"] == "oi"


# --- ausência de chave ---


async def test_sem_chave_levanta_erro_explicito(monkeypatch: pytest.MonkeyPatch):
    """Sem AI_API_KEY o erro tem que ser claro, e nao pode derrubar o import do
    modulo — por isso o client e' preguicoso."""
    import services.ai_service as ai_service

    _client.cache_clear()
    monkeypatch.setattr(ai_service.settings, "ai_api_key", "")
    with pytest.raises(AINotConfigured):
        _client()
    _client.cache_clear()
