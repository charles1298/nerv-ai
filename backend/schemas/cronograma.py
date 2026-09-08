"""Schemas do cronograma de estudos personalizado (seção 5.6)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Tipos de atividade que o aluno reconhece na tela. Fechado de propósito: com
# texto livre o modelo inventa rótulo novo a cada geração e a interface não
# consegue dar ícone nem cor consistente ao bloco.
TipoAtividade = Literal[
    "revisao",
    "exercicios",
    "leitura",
    "redacao",
    "simulado",
    "videoaula",
    "descanso",
]

DIAS_VALIDOS = {
    "segunda",
    "terça",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sábado",
    "sabado",
    "domingo",
}


class BlocoEstudo(BaseModel):
    """Um bloco de estudo dentro de um dia."""

    materia: str = Field(min_length=1, max_length=100)
    topico: str = Field(min_length=1, max_length=200)
    minutos: int = Field(ge=5, le=240)
    atividade: TipoAtividade
    descricao: str = Field(min_length=1, max_length=500)


class DiaEstudo(BaseModel):
    dia: str = Field(min_length=3, max_length=20)
    blocos: list[BlocoEstudo] = Field(min_length=1)

    @field_validator("dia")
    @classmethod
    def normaliza_dia(cls, v: str) -> str:
        """Aceita 'Segunda-feira' e devolve 'Segunda'.

        O modelo alterna entre as duas formas na mesma resposta; normalizar aqui
        evita que a interface tenha que adivinhar como agrupar.
        """
        limpo = v.strip().split("-")[0].strip()
        if limpo.lower() not in DIAS_VALIDOS:
            raise ValueError(f"dia inválido: {v}")
        return limpo.capitalize()

    @property
    def minutos_totais(self) -> int:
        return sum(b.minutos for b in self.blocos)


class SemanaEstudo(BaseModel):
    numero: int = Field(ge=1, le=52)
    foco: str = Field(min_length=1, max_length=300)
    dias: list[DiaEstudo] = Field(min_length=1)


class CronogramaGerado(BaseModel):
    """Saída do cronograma_agent, validada antes de persistir."""

    resumo: str = Field(min_length=1, max_length=1000)
    estrategia: str = Field(min_length=1, max_length=2000)
    semanas: list[SemanaEstudo] = Field(min_length=1)
    dicas: list[str] = Field(default_factory=list)

    def dias_acima_do_orcamento(self, minutos_por_dia: int, tolerancia: float = 1.2) -> list[str]:
        """Dias cujo total estoura o tempo que o aluno disse ter.

        É o erro mais destrutivo deste recurso: um plano que pede 3 horas de quem
        tem 30 minutos não é seguido, e o aluno conclui que não dá conta — quando
        na verdade o plano é que estava errado. A tolerância existe porque passar
        cinco minutos não invalida o dia.
        """
        teto = minutos_por_dia * tolerancia
        return [
            f"Semana {s.numero}, {d.dia}: {d.minutos_totais} min"
            for s in self.semanas
            for d in s.dias
            if d.minutos_totais > teto
        ]


class CronogramaCreateRequest(BaseModel):
    objetivo: str = Field(min_length=5, max_length=300)
    semanas: int = Field(ge=1, le=12)
    dias_por_semana: int = Field(ge=1, le=7)
    minutos_por_dia: int = Field(ge=15, le=240)
    materias: list[str] = Field(default_factory=list, max_length=10)


class CronogramaPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    objetivo: str
    semanas_total: int
    dias_por_semana: int
    minutos_por_dia: int
    materias_foco: list
    resumo: str
    estrategia: str
    semanas: list
    dicas: list
    created_at: datetime


class CronogramaResumoPublic(BaseModel):
    """Versão enxuta para a listagem — sem o corpo do plano.

    A lista carregaria dezenas de semanas por item sem isso, e a tela só mostra
    objetivo, data e tamanho.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID
    objetivo: str
    semanas_total: int
    dias_por_semana: int
    minutos_por_dia: int
    created_at: datetime
