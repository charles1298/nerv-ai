"""Schemas da avaliação de redação ENEM — espelham o output da seção 5.3."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ErroGramatical(BaseModel):
    trecho: str
    erro: str
    correcao: str


class AnaliseDetalhada(BaseModel):
    pontos_fortes: list[str] = Field(default_factory=list)
    pontos_fracos: list[str] = Field(default_factory=list)
    erros_gramaticais: list[ErroGramatical] = Field(default_factory=list)


class RedacaoAvaliacao(BaseModel):
    """Saída do redacao_agent, validada antes de persistir."""

    nota_total: int = Field(ge=0, le=1000)
    notas_por_criterio: dict[str, int]
    analise_detalhada: AnaliseDetalhada
    reescrita_sugerida: str
    nota_estimada_real_enem: str
    proximos_passos: list[str] = Field(default_factory=list)

    @field_validator("notas_por_criterio")
    @classmethod
    def validate_criterios(cls, v: dict[str, int]) -> dict[str, int]:
        expected = {"C1", "C2", "C3", "C4", "C5"}
        if set(v.keys()) != expected:
            raise ValueError(f"notas_por_criterio deve conter exatamente {expected}")
        for criterio, nota in v.items():
            if not 0 <= nota <= 200:
                raise ValueError(f"{criterio} fora do intervalo 0-200")
            if nota % 40 != 0:
                raise ValueError(f"{criterio} deve ser múltiplo de 40 (níveis do ENEM)")
        return v


class RedacaoSubmitRequest(BaseModel):
    theme: str = Field(min_length=5, max_length=500)
    content: str = Field(min_length=200, max_length=20000)


class EssayPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    theme: str
    content: str
    nota_total: int | None
    notas_por_criterio: dict | None
    analise_detalhada: dict | None
    reescrita_sugerida: str | None
    nota_estimada_real_enem: str | None
    proximos_passos: list | None
    submitted_at: datetime
