import enum
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.financeiro import FrequenciaPlano
from src.schemas.aluno import hoje
from src.schemas.base import SchemaEntrada
from src.schemas.tipos import DescricaoCobranca, IdBanco, ValorCentavos


class Situacao(enum.StrEnum):
    """O que o app mostra: o status guardado, com a vencida calculada na hora."""

    PENDENTE = "pendente"
    VENCIDA = "vencida"
    PAGA = "paga"
    CANCELADA = "cancelada"


def _conferir_dia(frequencia: FrequenciaPlano, dia: int) -> None:
    if frequencia == FrequenciaPlano.MENSAL and not 1 <= dia <= 31:
        raise ValueError("no plano mensal, o dia de vencimento vai de 1 a 31")
    if frequencia == FrequenciaPlano.SEMANAL and not 0 <= dia <= 6:
        raise ValueError(
            "no plano semanal, o dia de vencimento vai de 0 (segunda) a 6 (domingo)"
        )


class PlanoCriar(SchemaEntrada):
    """`dia_vencimento`: 1 a 31 no mensal (no mês mais curto, o último dia) e
    0 (segunda) a 6 (domingo) no semanal. Sem `fim`, vale até ser encerrado."""

    aluno_id: IdBanco
    descricao: DescricaoCobranca
    valor_centavos: ValorCentavos
    frequencia: FrequenciaPlano
    dia_vencimento: int
    inicio: date = Field(default_factory=hoje)
    fim: date | None = None

    @model_validator(mode="after")
    def _regras(self) -> Self:
        _conferir_dia(self.frequencia, self.dia_vencimento)
        if self.fim is not None and self.fim < self.inicio:
            raise ValueError("o fim não pode ser anterior ao início")
        return self


class PlanoAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado; `fim` nulo tira a data de fim. Vale para
    as cobranças ainda não vencidas."""

    descricao: DescricaoCobranca | None = None
    valor_centavos: ValorCentavos | None = None
    dia_vencimento: int | None = None
    fim: date | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        nulos = sorted(
            campo
            for campo in self.model_fields_set - {"fim"}
            if getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"campos que não podem ser nulos: {', '.join(nulos)}")
        return self


class CobrancaCriar(SchemaEntrada):
    aluno_id: IdBanco
    descricao: DescricaoCobranca
    valor_centavos: ValorCentavos
    vencimento: date


class CobrancaAtualizar(SchemaEntrada):
    """Só para cobranças pendentes. Só o que for enviado é alterado."""

    descricao: DescricaoCobranca | None = None
    valor_centavos: ValorCentavos | None = None
    vencimento: date | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        nulos = sorted(
            campo for campo in self.model_fields_set if getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"campos que não podem ser nulos: {', '.join(nulos)}")
        return self


class CobrancaPagar(SchemaEntrada):
    """Sem `paga_em`, vale o momento da baixa."""

    paga_em: datetime | None = None


class PlanoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    aluno_nome: str
    descricao: str
    valor_centavos: int
    frequencia: FrequenciaPlano
    dia_vencimento: int
    inicio: date
    fim: date | None
    criado_em: datetime


class CobrancaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    aluno_nome: str
    plano_id: int | None
    descricao: str
    valor_centavos: int
    vencimento: date
    situacao: Situacao
    paga_em: datetime | None
    criado_em: datetime


class ResumoResposta(BaseModel):
    """Totais do mês, pelo vencimento, em centavos."""

    mes: str
    recebido_centavos: int
    pendente_centavos: int
    vencido_centavos: int


class MinhaCobrancaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    valor_centavos: int
    vencimento: date
    situacao: Situacao
    paga_em: datetime | None
    professor_nome: str
    chave_pix: str | None
