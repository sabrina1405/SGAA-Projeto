from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.aluno import AlunoListaItem
from src.schemas.arquivo import ArquivoResposta
from src.schemas.base import SchemaEntrada
from src.schemas.recado import RecadoGrupoItem
from src.schemas.tipos import (
    IdBanco,
    IdsDeAlunos,
    IdsDeArquivos,
    IdsDeGrupos,
    NomePasta,
)


class PastaCriar(SchemaEntrada):
    """Sem `pasta_pai_id`, a pasta é raiz. Os destinatários só valem na raiz e
    alcançam todas as subpastas dela."""

    nome: NomePasta
    pasta_pai_id: IdBanco | None = None
    todos_alunos: bool = False
    todos_grupos: bool = False
    aluno_ids: IdsDeAlunos = Field(default_factory=list)
    grupo_ids: IdsDeGrupos = Field(default_factory=list)


class PastaAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado. `pasta_pai_id` nulo move a pasta para a
    raiz. As listas enviadas substituem os destinatários atuais."""

    nome: NomePasta | None = None
    pasta_pai_id: IdBanco | None = None
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
            for campo in self.model_fields_set - {"pasta_pai_id"}
            if getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"campos que não podem ser nulos: {', '.join(nulos)}")
        return self


class ArquivosDaPastaAdicionar(SchemaEntrada):
    arquivo_ids: IdsDeArquivos


class ArquivoDaPastaMover(SchemaEntrada):
    pasta_id: IdBanco


class PastaListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    total_subpastas: int
    total_arquivos: int
    criado_em: datetime


class PastaCaminhoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class PastaDetalheResposta(BaseModel):
    """Os destinatários são os da raiz, que valem para a árvore inteira."""

    id: int
    nome: str
    pasta_pai_id: int | None
    raiz_id: int
    caminho: list[PastaCaminhoItem]
    todos_alunos: bool
    todos_grupos: bool
    alunos: list[AlunoListaItem]
    grupos: list[RecadoGrupoItem]
    subpastas: list[PastaListaItem]
    arquivos: list[ArquivoResposta]
    criado_em: datetime


class MaterialListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    professor_nome: str
    total_subpastas: int
    total_arquivos: int


class MaterialDetalheResposta(BaseModel):
    id: int
    nome: str
    professor_nome: str
    caminho: list[PastaCaminhoItem]
    subpastas: list[PastaListaItem]
    arquivos: list[ArquivoResposta]
