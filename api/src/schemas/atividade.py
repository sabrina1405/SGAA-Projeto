from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from src.models.atividade import StatusEntrega
from src.schemas.aluno import AlunoListaItem
from src.schemas.arquivo import ArquivoResposta
from src.schemas.aula import DataHora
from src.schemas.base import SchemaEntrada
from src.schemas.recado import RecadoGrupoItem
from src.schemas.tipos import (
    AnexosDaAtividade,
    AnexosDaEntrega,
    IdsDeAlunos,
    IdsDeGrupos,
    TextoAtividade,
    TituloAtividade,
)


class SituacaoAtividade(StrEnum):
    PROXIMAS = "proximas"
    VENCIDAS = "vencidas"


class SituacaoEntrega(StrEnum):
    PROXIMAS = "proximas"
    VENCIDAS = "vencidas"
    ENTREGUES = "entregues"


class SituacaoMinhaAtividade(StrEnum):
    PROXIMAS = "proximas"
    VENCIDAS = "vencidas"
    REALIZADAS = "realizadas"


class AtividadeCriar(SchemaEntrada):
    """Precisa de ao menos um destinatário: alunos, grupos ou um dos "todos"."""

    titulo: TituloAtividade
    descricao: TextoAtividade
    liberar_em: AwareDatetime
    vence_em: AwareDatetime
    permite_envio_arquivo: bool = False
    todos_alunos: bool = False
    todos_grupos: bool = False
    aluno_ids: IdsDeAlunos = Field(default_factory=list)
    grupo_ids: IdsDeGrupos = Field(default_factory=list)
    arquivo_ids: AnexosDaAtividade = Field(default_factory=list)


class AtividadeAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado. As listas enviadas substituem as atuais."""

    titulo: TituloAtividade | None = None
    descricao: TextoAtividade | None = None
    liberar_em: AwareDatetime | None = None
    vence_em: AwareDatetime | None = None
    permite_envio_arquivo: bool | None = None
    todos_alunos: bool | None = None
    todos_grupos: bool | None = None
    aluno_ids: IdsDeAlunos | None = None
    grupo_ids: IdsDeGrupos | None = None
    arquivo_ids: AnexosDaAtividade | None = None

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


class EntregaSalvar(SchemaEntrada):
    """`arquivo_ids` enviado substitui os arquivos atuais; ausente, mantém."""

    resposta: TextoAtividade
    arquivo_ids: AnexosDaEntrega | None = None


class AtividadeListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    liberar_em: DataHora
    vence_em: DataHora
    permite_envio_arquivo: bool
    total_entregas: int


class AtividadeDetalheResposta(BaseModel):
    id: int
    titulo: str
    descricao: str
    liberar_em: DataHora
    vence_em: DataHora
    permite_envio_arquivo: bool
    todos_alunos: bool
    todos_grupos: bool
    alunos: list[AlunoListaItem]
    grupos: list[RecadoGrupoItem]
    anexos: list[ArquivoResposta]
    criado_em: datetime


class EntregaListaItem(BaseModel):
    """Uma linha por aluno e atividade. `status` nulo: o aluno ainda não entregou."""

    model_config = ConfigDict(from_attributes=True)

    atividade_id: int
    titulo: str
    vence_em: DataHora
    aluno_id: int
    aluno_nome: str
    status: StatusEntrega | None
    enviada_em: DataHora | None


class EntregaResposta(BaseModel):
    atividade_id: int
    aluno_id: int
    resposta: str
    status: StatusEntrega
    enviada_em: DataHora
    anexos: list[ArquivoResposta]


class MinhaAtividadeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    liberar_em: DataHora
    vence_em: DataHora
    permite_envio_arquivo: bool
    professor_nome: str
    status: StatusEntrega | None
    enviada_em: DataHora | None


class MinhaAtividadeDetalhe(BaseModel):
    id: int
    titulo: str
    descricao: str
    liberar_em: DataHora
    vence_em: DataHora
    permite_envio_arquivo: bool
    professor_nome: str
    criado_em: datetime
    anexos: list[ArquivoResposta]
    entrega: EntregaResposta | None
