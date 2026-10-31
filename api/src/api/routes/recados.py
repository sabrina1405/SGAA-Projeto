from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.api.deps import EnviadorPushDep, ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.recado import Recado
from src.schemas.aluno import AlunoListaItem, hoje
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.recado import (
    RecadoAtualizar,
    RecadoCriar,
    RecadoDetalheResposta,
    RecadoGeralResposta,
    RecadoGeralSalvar,
    RecadoGrupoItem,
    RecadoListaItem,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import (
    grupo_service,
    notificacao_service,
    recado_service,
    usuario_service,
)

router = APIRouter(prefix="/recados", tags=["Recados"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def _dados_recado(sessao: Session, recado: Recado) -> RecadoDetalheResposta:
    alunos = recado_service.listar_alunos_do_recado(sessao, recado)
    grupos = recado_service.listar_grupos_do_recado(sessao, recado)
    return RecadoDetalheResposta(
        id=recado.id,
        conteudo=recado.conteudo,
        data_inicio=recado.data_inicio,
        data_fim=recado.data_fim,
        todos_alunos=recado.todos_alunos,
        todos_grupos=recado.todos_grupos,
        alunos=[AlunoListaItem.model_validate(aluno) for aluno in alunos],
        grupos=[RecadoGrupoItem.model_validate(grupo) for grupo in grupos],
        criado_em=recado.criado_em,
    )


def _recado_nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Recado não encontrado"
    )


ERROS_DE_DESTINATARIO = (
    recado_service.RecadoInvalido,
    grupo_service.GruposInvalidos,
    usuario_service.AlunosInvalidos,
)


def _destinatarios_invalidos(
    erro: recado_service.RecadoInvalido
    | grupo_service.GruposInvalidos
    | usuario_service.AlunosInvalidos,
) -> CamposInvalidos:
    if isinstance(erro, recado_service.RecadoInvalido):
        return CamposInvalidos(erro.tipo, erro.mensagem, erro.campos)
    ids = ", ".join(str(item_id) for item_id in erro.ids)
    if isinstance(erro, usuario_service.AlunosInvalidos):
        return CamposInvalidos(
            "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_ids"]
        )
    return CamposInvalidos(
        "grupo_invalido", f"grupo não encontrado: {ids}", ["grupo_ids"]
    )


# As rotas do recado geral vêm antes de /{recado_id}.


@router.get("/geral")
def obter_recado_geral(
    professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[RecadoGeralResposta]:
    """`dados` nulo quando o painel está vazio."""
    recado_geral = recado_service.obter_recado_geral(sessao, professor)
    if recado_geral is None:
        return Resposta(mensagem="Recado geral vazio")
    return Resposta(
        mensagem="Recado geral encontrado",
        dados=RecadoGeralResposta.model_validate(recado_geral),
    )


@router.put("/geral")
def salvar_recado_geral(
    dados: RecadoGeralSalvar, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[RecadoGeralResposta]:
    """Cria ou substitui o recado geral, que todos os alunos veem."""
    recado_geral = recado_service.salvar_recado_geral(sessao, professor, dados.conteudo)
    return Resposta(
        mensagem="Recado geral salvo",
        dados=RecadoGeralResposta.model_validate(recado_geral),
    )


@router.delete("/geral")
def limpar_recado_geral(professor: ProfessorAtual, sessao: SessaoDep) -> Resposta[None]:
    recado_service.limpar_recado_geral(sessao, professor)
    return Resposta(mensagem="Recado geral limpo")


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_recado(
    dados: RecadoCriar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    enviador: EnviadorPushDep,
    tarefas: BackgroundTasks,
) -> Resposta[RecadoDetalheResposta]:
    """Precisa de ao menos um destinatário: alunos, grupos ou um dos "todos".

    Os alunos recebem um push quando o recado entra no período de exibição.
    """
    try:
        recado, notificacao_id = recado_service.criar_recado(
            sessao, professor, **dados.model_dump()
        )
    except ERROS_DE_DESTINATARIO as erro:
        raise _destinatarios_invalidos(erro) from None
    if recado.data_inicio <= hoje():
        tarefas.add_task(
            notificacao_service.enviar_sem_falhar, sessao, enviador, notificacao_id
        )
    return Resposta(mensagem="Recado criado", dados=_dados_recado(sessao, recado))


@router.get("")
def listar_recados(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[RecadoListaItem]]:
    """Histórico do professor, do mais novo ao mais antigo."""
    itens, total = recado_service.listar_recados(
        sessao, professor, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Recados listados",
        dados=Pagina(
            itens=[RecadoListaItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/{recado_id}")
def detalhar_recado(
    recado_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[RecadoDetalheResposta]:
    try:
        recado = recado_service.obter_recado(sessao, professor, recado_id)
    except recado_service.RecadoNaoEncontrado:
        raise _recado_nao_encontrado() from None
    return Resposta(mensagem="Recado encontrado", dados=_dados_recado(sessao, recado))


@router.patch("/{recado_id}")
def atualizar_recado(
    recado_id: IdNoCaminho,
    dados: RecadoAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[RecadoDetalheResposta]:
    """Altera só os campos enviados. As listas enviadas substituem os destinatários."""
    try:
        recado = recado_service.atualizar_recado(
            sessao, professor, recado_id, dados.model_dump(exclude_unset=True)
        )
    except recado_service.RecadoNaoEncontrado:
        raise _recado_nao_encontrado() from None
    except ERROS_DE_DESTINATARIO as erro:
        raise _destinatarios_invalidos(erro) from None
    return Resposta(mensagem="Recado atualizado", dados=_dados_recado(sessao, recado))


@router.delete("/{recado_id}")
def excluir_recado(
    recado_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[None]:
    try:
        recado_service.excluir_recado(sessao, professor, recado_id)
    except recado_service.RecadoNaoEncontrado:
        raise _recado_nao_encontrado() from None
    return Resposta(mensagem="Recado excluído")
