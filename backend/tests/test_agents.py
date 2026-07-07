"""Testes dos agentes — validação de schema, correção local e streaming mockado."""

import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

import agents.tutor_agent as tutor_agent
from agents.exercise_agent import grade_multiple_choice
from models import Exercise
from schemas.exercises import ExerciseContent

pytestmark = pytest.mark.asyncio

VALID_CONTENT = {
    "question": "Quanto é $2^3$?",
    "tipo": "multipla_escolha",
    "difficulty": 2,
    "alternatives": [
        {"label": "A", "text": "6", "is_correct": False},
        {"label": "B", "text": "8", "is_correct": True},
        {"label": "C", "text": "9", "is_correct": False},
    ],
    "correct_answer": "B",
    "step_by_step_solution": "Passo 1: $2^3 = 2 \\cdot 2 \\cdot 2$\nPortanto, 8.",
    "bncc_skill": "EF06MA03",
    "hints": ["Multiplique o 2 três vezes."],
    "common_mistakes": ["Confundir potência com multiplicação simples."],
}


def _exercise() -> Exercise:
    return Exercise(
        id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        content=VALID_CONTENT,
        difficulty=2,
        tipo="multipla_escolha",
    )


async def test_exercise_content_valid():
    content = ExerciseContent.model_validate(VALID_CONTENT)
    assert content.correct_answer == "B"


async def test_exercise_content_rejects_no_correct_alternative():
    broken = {**VALID_CONTENT, "alternatives": [
        {"label": "A", "text": "6", "is_correct": False},
        {"label": "B", "text": "8", "is_correct": False},
    ]}
    with pytest.raises(ValidationError):
        ExerciseContent.model_validate(broken)


async def test_exercise_content_rejects_mismatched_answer():
    broken = {**VALID_CONTENT, "correct_answer": "A"}
    with pytest.raises(ValidationError):
        ExerciseContent.model_validate(broken)


async def test_grade_correct_answer():
    is_correct, score, feedback = grade_multiple_choice(_exercise(), "b")
    assert is_correct is True
    assert score == 10.0
    assert "correta" in feedback.lower()


async def test_grade_wrong_answer():
    is_correct, score, feedback = grade_multiple_choice(_exercise(), "A")
    assert is_correct is False
    assert score == 0.0
    assert "B" in feedback


async def test_chat_streams_and_persists(
    client: AsyncClient, student_token: str, monkeypatch: pytest.MonkeyPatch
):
    """Fluxo completo: criar sessão → chat (modelo mockado) → mensagens persistidas."""

    async def fake_stream(system_prompt, messages, student_id, max_tokens=4096):
        assert "NERV" in system_prompt
        for token in ["Olá! ", "Vamos ", "estudar?"]:
            yield token

    monkeypatch.setattr(tutor_agent, "stream_tutor_response", fake_stream)

    headers = {"Authorization": f"Bearer {student_token}"}
    session_resp = await client.post("/sessions", headers=headers, json={})
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    async with client.stream(
        "POST", f"/sessions/{session_id}/chat", headers=headers,
        json={"content": "Me explica frações?"},
    ) as resp:
        assert resp.status_code == 200
        body = ""
        async for chunk in resp.aiter_text():
            body += chunk
    assert "Olá!" in body
    assert "[DONE]" in body

    messages = await client.get(f"/sessions/{session_id}/messages", headers=headers)
    roles = [m["role"] for m in messages.json()]
    assert roles == ["user", "assistant"]
    assert messages.json()[1]["content"] == "Olá! Vamos estudar?"


async def test_chat_requires_own_session(client: AsyncClient, student_token: str):
    headers = {"Authorization": f"Bearer {student_token}"}
    resp = await client.post(
        f"/sessions/{uuid.uuid4()}/chat", headers=headers, json={"content": "oi"}
    )
    assert resp.status_code == 404
