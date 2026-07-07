"""Schemas Pydantic de exercícios — espelham o schema de saída da seção 5.2."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TipoExercicio = Literal["multipla_escolha", "dissertativa", "calculo", "redacao"]


class Alternative(BaseModel):
    label: str = Field(pattern=r"^[A-E]$")
    text: str
    is_correct: bool


class ExerciseContent(BaseModel):
    """Conteúdo gerado pelo exercise_agent — validado antes de persistir."""

    question: str
    tipo: TipoExercicio
    difficulty: int = Field(ge=1, le=5)
    alternatives: list[Alternative] = Field(default_factory=list)
    correct_answer: str | None = None
    step_by_step_solution: str
    bncc_skill: str | None = None
    hints: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_multipla_escolha(self) -> "ExerciseContent":
        if self.tipo == "multipla_escolha":
            if len(self.alternatives) < 2:
                raise ValueError("Múltipla escolha exige ao menos 2 alternativas")
            correct = [a.label for a in self.alternatives if a.is_correct]
            if len(correct) != 1:
                raise ValueError("Múltipla escolha exige exatamente 1 alternativa correta")
            if self.correct_answer != correct[0]:
                raise ValueError("correct_answer deve apontar para a alternativa marcada como correta")
        return self


class ExerciseGenerateRequest(BaseModel):
    topic_id: uuid.UUID
    tipo: TipoExercicio = "multipla_escolha"


class ExercisePublic(BaseModel):
    """Exercício exposto ao aluno — sem gabarito nem solução."""

    id: uuid.UUID
    topic_id: uuid.UUID | None
    question: str
    tipo: str | None
    difficulty: int
    alternatives: list[dict]
    hints: list[str]
    created_at: datetime


class AttemptRequest(BaseModel):
    answer: str
    time_spent_seconds: int | None = Field(default=None, ge=0)


class AttemptResult(BaseModel):
    attempt_id: uuid.UUID
    is_correct: bool
    score: float
    feedback: str
    step_by_step_solution: str
