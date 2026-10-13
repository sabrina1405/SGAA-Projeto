from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.aluno import AlunoListaItem
from src.schemas.base import SchemaEntrada
from src.schemas.tipos import DescricaoGrupo, IdsDeAlunos, TituloGrupo


class GrupoCriar(SchemaEntrada):
    titulo: TituloGrupo
    descricao: DescricaoGrupo | None = None
    aluno_ids: IdsDeAlunos = Field(default_factory=list)


class GrupoAtualizar(SchemaEntrada):
    """Só o que for enviado é alterado. `descricao` nula apaga a descrição."""

    titulo: TituloGrupo | None = None
    descricao: DescricaoGrupo | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        if "titulo" in self.model_fields_set and self.titulo is None:
            raise ValueError("o título não pode ser nulo")
        return self


class GrupoAlunosAdicionar(SchemaEntrada):
    aluno_ids: Annotated[IdsDeAlunos, Field(min_length=1)]


class GrupoListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None
    total_alunos: int


class GrupoDetalheResposta(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    alunos: list[AlunoListaItem]
