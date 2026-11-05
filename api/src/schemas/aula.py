from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from src.models.aula import StatusAula, StatusParticipacao
from src.schemas.aluno import HORARIO_DE_BRASILIA
from src.schemas.base import SchemaEntrada
from src.schemas.tipos import (
    AnotacoesAula,
    DescricaoAula,
    IdBanco,
    IdsDeAlunos,
    IdsDeGrupos,
    MotivoCancelamento,
    TituloAula,
)


class Escopo(StrEnum):
    """Quais ocorrências de uma série a edição ou o cancelamento alcança."""

    ESTA = "esta"
    ESTA_E_SEGUINTES = "esta_e_seguintes"


def _no_horario_de_brasilia(valor: datetime) -> datetime:
    return valor.astimezone(HORARIO_DE_BRASILIA)


# As respostas sempre trazem o horário de Brasília, com o deslocamento.
DataHora = Annotated[datetime, AfterValidator(_no_horario_de_brasilia)]


class AulaCriar(SchemaEntrada):
    """Precisa de ao menos um aluno, direto ou por um grupo.

    Com `repetir_semanalmente`, cria uma aula por semana até `repetir_ate`.
    """

    titulo: TituloAula
    descricao: DescricaoAula | None = None
    anotacoes: AnotacoesAula | None = None
    inicio: AwareDatetime
    fim: AwareDatetime
    aluno_ids: IdsDeAlunos = Field(default_factory=list)
    grupo_ids: IdsDeGrupos = Field(default_factory=list)
    repetir_semanalmente: bool = False
    repetir_ate: date | None = None
    reposicao_de_aula_id: IdBanco | None = None


class AulaAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado. `descricao` e `anotacoes` nulas são apagadas."""

    titulo: TituloAula | None = None
    descricao: DescricaoAula | None = None
    anotacoes: AnotacoesAula | None = None
    inicio: AwareDatetime | None = None
    fim: AwareDatetime | None = None
    # O cancelamento tem rota própria.
    status: Literal[StatusAula.AGENDADA, StatusAula.REALIZADA] | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        nulos = sorted(
            campo
            for campo in self.model_fields_set - {"descricao", "anotacoes"}
            if getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"campos que não podem ser nulos: {', '.join(nulos)}")
        return self


class AulaAlunosAdicionar(SchemaEntrada):
    aluno_ids: IdsDeAlunos = Field(default_factory=list)
    grupo_ids: IdsDeGrupos = Field(default_factory=list)

    @model_validator(mode="after")
    def _algum_destinatario(self) -> Self:
        if not (self.aluno_ids or self.grupo_ids):
            raise ValueError("informe ao menos um aluno ou grupo")
        return self


class AulaCancelar(SchemaEntrada):
    """`repor` deixa uma reposição pendente para cada aluno da aula."""

    motivo: MotivoCancelamento | None = None
    repor: bool = False


class ParticipacaoCancelar(SchemaEntrada):
    motivo: MotivoCancelamento | None = None


class AulaAlunoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    status: StatusParticipacao


class AulaListaItem(BaseModel):
    id: int
    titulo: str
    inicio: DataHora
    fim: DataHora
    status: StatusAula
    serie_id: int | None
    alunos: list[AulaAlunoItem]


class AulaAlunoDetalhe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    email: str
    telefone: str
    status: StatusParticipacao
    motivo_cancelamento: str | None
    repor: bool


class AulaGrupoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str


class AulaDetalheResposta(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    anotacoes: str | None
    inicio: DataHora
    fim: DataHora
    status: StatusAula
    motivo_cancelamento: str | None
    serie_id: int | None
    reposicao_de_aula_id: int | None
    alunos: list[AulaAlunoDetalhe]
    grupos: list[AulaGrupoItem]
    criado_em: datetime


class ReposicaoPendenteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aula_id: int
    titulo: str
    inicio: DataHora
    fim: DataHora
    aluno_id: int
    aluno_nome: str
    # "aluno" quando ele cancelou a participação; "professor" quando a aula
    # foi cancelada.
    cancelada_por: Literal["aluno", "professor"]
    motivo_cancelamento: str | None


class AgendaItem(BaseModel):
    """Aula na agenda do aluno, sem as anotações do professor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None
    inicio: DataHora
    fim: DataHora
    status: StatusAula
    participacao: StatusParticipacao
    motivo_cancelamento: str | None
    professor_nome: str
