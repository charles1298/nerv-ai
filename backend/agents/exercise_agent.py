"""Agente de geração adaptativa de exercícios (seção 5.2 do CLAUDE.md)."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Exercise, ExerciseAttempt, Topic, User
from schemas.exercises import ExerciseContent, TipoExercicio
from services.ai_service import complete_json

logger = structlog.get_logger()

EXERCISE_SYSTEM_PROMPT = """Você é o gerador de exercícios do NERV AI, plataforma educacional brasileira alinhada à BNCC.
Gere exercícios pedagogicamente sólidos, com enunciado claro, no nível de dificuldade pedido.
Para alunos de 3º ano do EM, use o estilo ENEM: texto motivador, 5 alternativas (A-E), contextualização.
Use contextos brasileiros (cotidiano, regiões, cultura) sempre que possível.
Para matemática, use notação LaTeX inline ($...$).

Responda APENAS com um objeto JSON válido, exatamente neste formato:
{
  "question": "Texto completo da questão",
  "tipo": "multipla_escolha | dissertativa | calculo | redacao",
  "difficulty": 3,
  "alternatives": [
    {"label": "A", "text": "...", "is_correct": false},
    {"label": "B", "text": "...", "is_correct": true},
    {"label": "C", "text": "...", "is_correct": false},
    {"label": "D", "text": "...", "is_correct": false},
    {"label": "E", "text": "...", "is_correct": false}
  ],
  "correct_answer": "B",
  "step_by_step_solution": "Passo 1: ...\\nPasso 2: ...\\nPortanto...",
  "bncc_skill": "EF09MA07",
  "hints": ["Pensa na fórmula de...", "Lembre que..."],
  "common_mistakes": ["Confundir X com Y", "Esquecer de..."]
}
Para tipos sem alternativas (dissertativa, calculo, redacao), retorne "alternatives": [] e "correct_answer": null."""


async def compute_adaptive_difficulty(db: AsyncSession, student_id, topic_id) -> int:
    """Nível N+1: um pouco além do conforto atual do aluno no tópico.

    Baseado na taxa de acerto das últimas tentativas; sem histórico, começa no nível 2.
    """
    rows = await db.execute(
        select(ExerciseAttempt.is_correct, Exercise.difficulty)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(ExerciseAttempt.student_id == student_id, Exercise.topic_id == topic_id)
        .order_by(ExerciseAttempt.attempted_at.desc())
        .limit(10)
    )
    attempts = rows.all()
    if not attempts:
        return 2

    correct_rate = sum(1 for is_correct, _ in attempts if is_correct) / len(attempts)
    current_level = max(difficulty for _, difficulty in attempts)
    if correct_rate >= 0.8:
        return min(current_level + 1, 5)
    if correct_rate <= 0.4:
        return max(current_level - 1, 1)
    return current_level


async def generate_exercise(
    db: AsyncSession,
    student: User,
    topic: Topic,
    tipo: TipoExercicio,
) -> Exercise:
    """Gera, valida e persiste um exercício adaptado ao aluno."""
    difficulty = await compute_adaptive_difficulty(db, student.id, topic.id)
    enem_style = student.grade == "3ano_em"

    user_prompt = (
        f"Gere 1 exercício do tipo '{tipo}' sobre o tópico '{topic.name}' "
        f"(matéria: {topic.subject.name}, habilidade BNCC: {topic.bncc_skill_code or 'não mapeada'}).\n"
        f"Série do aluno: {student.grade or 'não informada'}.\n"
        f"Nível de dificuldade alvo: {difficulty} (escala 1-5).\n"
        + ("Use o estilo ENEM completo (texto motivador + 5 alternativas).\n" if enem_style else "")
    )

    raw = await complete_json(
        system_prompt=EXERCISE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        student_id=str(student.id),
    )
    content = ExerciseContent.model_validate(raw)

    exercise = Exercise(
        student_id=student.id,
        topic_id=topic.id,
        content=content.model_dump(),
        difficulty=content.difficulty,
        tipo=content.tipo,
        source="ai",
    )
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    logger.info(
        "exercise_generated",
        exercise_id=str(exercise.id),
        student_id=str(student.id),
        topic=topic.name,
        difficulty=content.difficulty,
    )
    return exercise


def grade_multiple_choice(exercise: Exercise, answer: str) -> tuple[bool, float, str]:
    """Corrige múltipla escolha localmente (sem chamada ao modelo)."""
    content = ExerciseContent.model_validate(exercise.content)
    is_correct = answer.strip().upper() == (content.correct_answer or "").upper()
    score = 10.0 if is_correct else 0.0
    if is_correct:
        feedback = "Resposta correta! Confira a resolução passo a passo para consolidar o raciocínio."
    else:
        mistakes = " ".join(content.common_mistakes[:2])
        feedback = (
            f"Resposta incorreta — a alternativa certa é {content.correct_answer}. "
            f"Erros comuns nessa questão: {mistakes or 'reveja a resolução com atenção.'}"
        )
    return is_correct, score, feedback
