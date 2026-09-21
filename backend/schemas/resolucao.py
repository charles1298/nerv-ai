"""Schemas da resolução de exercícios com explicação (seção 5.7)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

OrigemResolucao = Literal["texto", "foto"]

# Quanto o sistema confia na própria leitura do enunciado. Importa sobretudo na
# foto: letra ruim, sombra ou recorte cortando a questão levam a uma resolução
# correta para o enunciado errado, e o aluno precisa saber disso.
NivelConfianca = Literal["alta", "media", "baixa"]


class PassoResolucao(BaseModel):
    """Um passo da resolução.

    `titulo` e `explicacao` são separados de propósito: o aluno bate o olho nos
    títulos para achar onde travou, sem reler a resolução inteira.
    """

    numero: int = Field(ge=1, le=20)
    titulo: str = Field(min_length=1, max_length=150)
    explicacao: str = Field(min_length=1, max_length=1500)
    # LaTeX do cálculo daquele passo. Opcional: passo de interpretação de texto
    # não tem conta nenhuma.
    expressao: str | None = Field(default=None, max_length=500)


class ResolucaoGerada(BaseModel):
    """Saída do resolucao_agent, validada antes de persistir."""

    # O que o sistema entendeu do enunciado. Na foto é o item mais importante da
    # tela: se a leitura saiu errada, o aluno percebe aqui em vez de estudar uma
    # resolução que não é do exercício dele.
    enunciado_interpretado: str = Field(min_length=1, max_length=3000)
    materia: str = Field(min_length=1, max_length=100)
    topico: str = Field(min_length=1, max_length=200)

    passos: list[PassoResolucao] = Field(min_length=1)
    resposta_final: str = Field(min_length=1, max_length=1000)

    # A parte que faz isso ensinar em vez de só entregar a resposta.
    conceito: str = Field(min_length=1, max_length=2000)
    erros_comuns: list[str] = Field(default_factory=list)
    como_conferir: str = Field(min_length=1, max_length=1500)
    exercicio_parecido: str = Field(min_length=1, max_length=1500)

    confianca: NivelConfianca = "alta"

    def passos_ordenados(self) -> list[PassoResolucao]:
        """Ordena e renumera os passos.

        O modelo às vezes devolve a lista fora de ordem ou repetindo o número 1.
        Como a tela mostra o número em destaque, isso apareceria direto para o
        aluno.
        """
        ordenados = sorted(self.passos, key=lambda p: p.numero)
        return [p.model_copy(update={"numero": i}) for i, p in enumerate(ordenados, start=1)]


class ResolucaoTextoRequest(BaseModel):
    enunciado: str = Field(min_length=10, max_length=5000)
    # O aluno pode dizer onde travou; entra no prompt para a explicação focar ali.
    duvida: str = Field(default="", max_length=500)


class ResolucaoPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    origem: OrigemResolucao
    enunciado: str
    imagem_url: str | None
    enunciado_interpretado: str
    materia: str
    topico: str
    passos: list
    resposta_final: str
    conceito: str
    erros_comuns: list
    como_conferir: str
    exercicio_parecido: str
    confianca: str
    created_at: datetime


class ResolucaoResumoPublic(BaseModel):
    """Versão enxuta para a listagem — sem os passos nem os textos longos."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    origem: OrigemResolucao
    materia: str
    topico: str
    enunciado_interpretado: str
    resposta_final: str
    created_at: datetime
