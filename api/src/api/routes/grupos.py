from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.api.deps import ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.grupo import Grupo
from src.schemas.aluno import AlunoListaItem
from src.schemas.grupo import (
    GrupoAlunosAdicionar,
    GrupoAtualizar,
    GrupoCriar,
    GrupoDetalheResposta,
    GrupoListaItem,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import grupo_service

router = APIRouter(prefix="/grupos", tags=["Grupos"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def _dados_grupo(sessao: Session, grupo: Grupo) -> GrupoDetalheResposta:
    alunos = grupo_service.listar_alunos_do_grupo(sessao, grupo)
    return GrupoDetalheResposta(
        id=grupo.id,
        titulo=grupo.titulo,
        descricao=grupo.descricao,
        alunos=[AlunoListaItem.model_validate(aluno) for aluno in alunos],
    )


def _grupo_nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado"
    )


def _alunos_invalidos(erro: grupo_service.AlunosInvalidos) -> CamposInvalidos:
    ids = ", ".join(str(aluno_id) for aluno_id in erro.ids)
    return CamposInvalidos(
        "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_ids"]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_grupo(
    dados: GrupoCriar, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[GrupoDetalheResposta]:
    """Só o título é obrigatório; os alunos podem ser adicionados depois."""
    try:
        grupo = grupo_service.criar_grupo(
            sessao,
            professor,
            titulo=dados.titulo,
            descricao=dados.descricao,
            aluno_ids=dados.aluno_ids,
        )
    except grupo_service.AlunosInvalidos as erro:
        raise _alunos_invalidos(erro) from None
    return Resposta(mensagem="Grupo criado", dados=_dados_grupo(sessao, grupo))


@router.get("")
def listar_grupos(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[GrupoListaItem]]:
    """Grupos do professor, em ordem alfabética de título."""
    itens, total = grupo_service.listar_grupos(
        sessao, professor, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Grupos listados",
        dados=Pagina(
            itens=[GrupoListaItem.model_validate(item) for item in itens], total=total
        ),
    )


@router.get("/{grupo_id}")
def detalhar_grupo(
    grupo_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[GrupoDetalheResposta]:
    try:
        grupo = grupo_service.obter_grupo(sessao, professor, grupo_id)
    except grupo_service.GrupoNaoEncontrado:
        raise _grupo_nao_encontrado() from None
    return Resposta(mensagem="Grupo encontrado", dados=_dados_grupo(sessao, grupo))


@router.patch("/{grupo_id}")
def atualizar_grupo(
    grupo_id: IdNoCaminho,
    dados: GrupoAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[GrupoDetalheResposta]:
    """Altera só os campos enviados. `descricao` nula apaga a descrição."""
    try:
        grupo = grupo_service.atualizar_grupo(
            sessao, professor, grupo_id, dados.model_dump(exclude_unset=True)
        )
    except grupo_service.GrupoNaoEncontrado:
        raise _grupo_nao_encontrado() from None
    return Resposta(mensagem="Grupo atualizado", dados=_dados_grupo(sessao, grupo))


@router.delete("/{grupo_id}")
def excluir_grupo(
    grupo_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[None]:
    try:
        grupo_service.excluir_grupo(sessao, professor, grupo_id)
    except grupo_service.GrupoNaoEncontrado:
        raise _grupo_nao_encontrado() from None
    return Resposta(mensagem="Grupo excluído")


@router.post("/{grupo_id}/alunos")
def adicionar_alunos(
    grupo_id: IdNoCaminho,
    dados: GrupoAlunosAdicionar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[GrupoDetalheResposta]:
    """Quem já está no grupo é ignorado. Se algum id for inválido, nenhum entra."""
    try:
        grupo = grupo_service.adicionar_alunos(
            sessao, professor, grupo_id, dados.aluno_ids
        )
    except grupo_service.GrupoNaoEncontrado:
        raise _grupo_nao_encontrado() from None
    except grupo_service.AlunosInvalidos as erro:
        raise _alunos_invalidos(erro) from None
    return Resposta(mensagem="Alunos adicionados", dados=_dados_grupo(sessao, grupo))


@router.delete("/{grupo_id}/alunos/{aluno_id}")
def remover_aluno(
    grupo_id: IdNoCaminho,
    aluno_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[None]:
    try:
        grupo_service.remover_aluno(sessao, professor, grupo_id, aluno_id)
    except grupo_service.GrupoNaoEncontrado:
        raise _grupo_nao_encontrado() from None
    except grupo_service.AlunoForaDoGrupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não está no grupo"
        ) from None
    return Resposta(mensagem="Aluno removido do grupo")
