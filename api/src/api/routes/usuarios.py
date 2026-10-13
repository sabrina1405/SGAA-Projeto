from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.api.deps import EnviadorEmailDep, ProfessorAtual, SessaoDep
from src.schemas.aluno import AlunoDetalheResposta, AlunoListaItem, PerfilAlunoDados
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO, Busca
from src.schemas.usuario import AlunoCriar, UsuarioResposta
from src.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/alunos", status_code=status.HTTP_201_CREATED)
def criar_aluno(
    dados: AlunoCriar, _: ProfessorAtual, sessao: SessaoDep, enviador: EnviadorEmailDep
) -> Resposta[UsuarioResposta]:
    try:
        usuario = usuario_service.criar_aluno(
            sessao, enviador, nome_completo=dados.nome_completo, email=dados.email
        )
    except usuario_service.EmailJaCadastrado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado"
        ) from None
    except usuario_service.FalhaEnvioEmail:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar o e-mail de acesso. Tente novamente.",
        ) from None
    return Resposta(
        mensagem="Aluno cadastrado", dados=UsuarioResposta.model_validate(usuario)
    )


@router.get("/alunos")
def listar_alunos(
    _: ProfessorAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
    busca: Annotated[Busca | None, Query()] = None,
) -> Resposta[Pagina[AlunoListaItem]]:
    """Alunos que concluíram o primeiro acesso, em ordem alfabética.

    `busca` procura um trecho no nome ou no e-mail, sem diferenciar maiúsculas
    nem acentos.
    """
    itens, total = usuario_service.listar_alunos(
        sessao, pagina=pagina, tamanho=tamanho, busca=busca
    )
    return Resposta(
        mensagem="Alunos listados",
        dados=Pagina(
            itens=[AlunoListaItem.model_validate(item) for item in itens], total=total
        ),
    )


@router.get("/alunos/{aluno_id}")
def detalhar_aluno(
    aluno_id: Annotated[int, Path(ge=1, le=ID_MAXIMO)],
    _: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[AlunoDetalheResposta]:
    """`aulas` e `pagamentos` ainda vêm sempre vazios."""
    try:
        usuario, aluno = usuario_service.obter_aluno(sessao, aluno_id)
    except usuario_service.AlunoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado"
        ) from None
    return Resposta(
        mensagem="Aluno encontrado",
        dados=AlunoDetalheResposta(
            id=usuario.id,
            nome_completo=usuario.nome_completo,
            email=usuario.email,
            primeiro_acesso_concluido=usuario.senha is not None,
            perfil=PerfilAlunoDados.model_validate(aluno) if aluno else None,
        ),
    )
