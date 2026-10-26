from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.aluno import AlunoListaItem, hoje
from src.schemas.base import SchemaEntrada
from src.schemas.tipos import ConteudoRecado, IdsDeAlunos, IdsDeGrupos


class RecadoGeralSalvar(SchemaEntrada):
    conteudo: ConteudoRecado


class RecadoCriar(SchemaEntrada):
    """Sem `data_fim`, o recado fica no mural até ser excluído."""

    conteudo: ConteudoRecado
    data_inicio: date = Field(default_factory=hoje)
    data_fim: date | None = None
    todos_alunos: bool = False
    todos_grupos: bool = False
    aluno_ids: IdsDeAlunos = Field(default_factory=list)
    grupo_ids: IdsDeGrupos = Field(default_factory=list)


class RecadoAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado. `data_fim` nula tira a data de fim.

    As listas enviadas substituem os destinatários atuais.
    """

    conteudo: ConteudoRecado | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    todos_alunos: bool | None = None
    todos_grupos: bool | None = None
    aluno_ids: IdsDeAlunos | None = None
    grupo_ids: IdsDeGrupos | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        nulos = sorted(
            campo
            for campo in self.model_fields_set - {"data_fim"}
            if getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"campos que não podem ser nulos: {', '.join(nulos)}")
        return self


class RecadoGeralResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conteudo: str
    atualizado_em: datetime


class RecadoGeralMuralItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    professor_nome: str
    conteudo: str
    atualizado_em: datetime


class RecadoGrupoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str


class RecadoListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conteudo: str
    data_inicio: date
    data_fim: date | None
    todos_alunos: bool
    todos_grupos: bool
    total_alunos: int
    total_grupos: int
    criado_em: datetime


class RecadoDetalheResposta(BaseModel):
    id: int
    conteudo: str
    data_inicio: date
    data_fim: date | None
    todos_alunos: bool
    todos_grupos: bool
    alunos: list[AlunoListaItem]
    grupos: list[RecadoGrupoItem]
    criado_em: datetime


class RecadoMuralItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conteudo: str
    data_inicio: date
    data_fim: date | None
    professor_nome: str
    criado_em: datetime
