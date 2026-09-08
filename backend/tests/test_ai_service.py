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


# --- LaTeX dentro do JSON ---
#
# Estes são os casos que quebravam a geração de exercícios de juros e
# porcentagem de forma reproduzível: o modelo escreve a fórmula dentro da
# string, e a barra do LaTeX não é escape JSON válido.


async def test_latex_com_barra_solta_e_reparado():
    r"""`\%` não é escape JSON válido e invalidaria o documento inteiro."""
    raw = r'{"question": "juros de $2\%$ ao mês"}'
    assert extract_json(raw)["question"] == r"juros de $2\%$ ao mês"


async def test_cifrao_e_virgula_fina_do_latex():
    r"""Dinheiro em LaTeX: `R\$\,500,00` traz duas barras inválidas seguidas."""
    raw = r'{"question": "emprestou R\$\,500,00 ao irmão"}'
    assert extract_json(raw)["question"] == r"emprestou R\$\,500,00 ao irmão"


async def test_barra_ja_escapada_nao_e_dobrada():
    r"""`\\` é escape válido: reparar de novo viraria barra dupla no texto."""
    raw = '{"formula": "2 \\\\cdot 3"}'
    assert extract_json(raw)["formula"] == r"2 \cdot 3"


async def test_escapes_validos_seguem_funcionando():
    r"""Reparo não pode estragar \n, \t nem \" legítimos."""
    raw = '{"texto": "linha1\\nlinha2\\ttab e aspas \\" ok"}'
    assert extract_json(raw)["texto"] == 'linha1\nlinha2\ttab e aspas " ok'


async def test_unicode_escapado_sobrevive():
    raw = '{"texto": "caf\\u00e9 com a\\u00e7\\u00facar"}'
    assert extract_json(raw)["texto"] == "café com açúcar"


async def test_latex_dentro_de_cerca_de_codigo():
    """Os dois problemas juntos: cerca de código e barra solta."""
    raw = '```json\n{"q": "a área é $x^2\\,cm^2$"}\n```'
    assert extract_json(raw)["q"] == r"a área é $x^2\,cm^2$"


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
