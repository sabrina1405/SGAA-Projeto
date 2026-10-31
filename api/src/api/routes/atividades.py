from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.api.deps import EnviadorPushDep, ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.atividade import Atividade, EntregaAtividade
from src.schemas.aluno import AlunoListaItem
from src.schemas.arquivo import ArquivoResposta
from src.schemas.atividade import (
    AtividadeAtualizar,
    AtividadeCriar,
    AtividadeDetalheResposta,
    AtividadeListaItem,
    EntregaListaItem,
    EntregaResposta,
    SituacaoAtividade,
    SituacaoEntrega,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.recado import RecadoGrupoItem
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import (
    arquivo_service,
    atividade_service,
    grupo_service,
    notificacao_service,
    usuario_service,
)

router = APIRouter(prefix="/atividades", tags=["Atividades"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]

ERROS_DA_ATIVIDADE = (
    atividade_service.AtividadeInvalida,
    usuario_service.AlunosInvalidos,
    grupo_service.GruposInvalidos,
    arquivo_service.ArquivosInvalidos,
)


def _atividade_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada"
    )


def _traduzir(erro: Exception) -> CamposInvalidos:
    if isinstance(erro, atividade_service.AtividadeInvalida):
        return CamposInvalidos(erro.tipo, erro.mensagem, erro.campos)
    ids = ", ".join(str(item_id) for item_id in erro.ids)
    if isinstance(erro, usuario_service.AlunosInvalidos):
        return CamposInvalidos(
            "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_ids"]
        )
    if isinstance(erro, grupo_service.GruposInvalidos):
        return CamposInvalidos(
            "grupo_invalido", f"grupo não encontrado: {ids}", ["grupo_ids"]
        )
    return CamposInvalidos(
        "arquivo_invalido", f"arquivo inválido: {ids}", ["arquivo_ids"]
    )


def _dados_atividade(sessao: Session, atividade: Atividade) -> AtividadeDetalheResposta:
    alunos = atividade_service.listar_alunos_da_atividade(sessao, atividade)
    grupos = atividade_service.listar_grupos_da_atividade(sessao, atividade)
    anexos = atividade_service.listar_anexos(sessao, atividade)
    return AtividadeDetalheResposta(
        id=atividade.id,
        titulo=atividade.titulo,
        descricao=atividade.descricao,
        liberar_em=atividade.liberar_em,
        vence_em=atividade.vence_em,
        permite_envio_arquivo=atividade.permite_envio_arquivo,
        todos_alunos=atividade.todos_alunos,
        todos_grupos=atividade.todos_grupos,
        alunos=[AlunoListaItem.model_validate(aluno) for aluno in alunos],
        grupos=[RecadoGrupoItem.model_validate(grupo) for grupo in grupos],
        anexos=[ArquivoResposta.model_validate(anexo) for anexo in anexos],
        criado_em=atividade.criado_em,
    )


def dados_entrega(sessao: Session, entrega: EntregaAtividade) -> EntregaResposta:
    anexos = atividade_service.listar_anexos_da_entrega(sessao, entrega)
    return EntregaResposta(
        atividade_id=entrega.atividade_id,
        aluno_id=entrega.aluno_id,
        resposta=entrega.resposta,
        status=entrega.status,
        enviada_em=entrega.enviada_em,
        anexos=[ArquivoResposta.model_validate(anexo) for anexo in anexos],
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_atividade(
    dados: AtividadeCriar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    enviador: EnviadorPushDep,
    tarefas: BackgroundTasks,
) -> Resposta[AtividadeDetalheResposta]:
    """Os arquivos sobem antes, em `/arquivos`, e entram aqui em `arquivo_ids`.

    Os alunos recebem um push na liberação e lembretes antes do vencimento.
    """
    try:
        atividade, notificacao_id = atividade_service.criar_atividade(
            sessao, professor, **dados.model_dump()
        )
    except ERROS_DA_ATIVIDADE as erro:
        raise _traduzir(erro) from None
    if notificacao_id is not None:
        tarefas.add_task(
            notificacao_service.enviar_sem_falhar, sessao, enviador, notificacao_id
        )
    return Resposta(
        mensagem="Atividade criada", dados=_dados_atividade(sessao, atividade)
    )


@router.get("")
def listar_atividades(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    situacao: SituacaoAtividade | None = None,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[AtividadeListaItem]]:
    """Da que vence antes à que vence depois, com `total_entregas` de cada uma."""
    itens, total = atividade_service.listar_atividades(
        sessao, professor, situacao=situacao, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Atividades listadas",
        dados=Pagina(
            itens=[AtividadeListaItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


# Antes de /{atividade_id}.
@router.get("/entregas")
def listar_entregas(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    situacao: SituacaoEntrega | None = None,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[EntregaListaItem]]:
    """Uma linha por aluno e atividade. `status` nulo: o aluno ainda não entregou."""
    itens, total = atividade_service.listar_entregas(
        sessao, professor, situacao=situacao, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Entregas listadas",
        dados=Pagina(
            itens=[EntregaListaItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/{atividade_id}")
def detalhar_atividade(
    atividade_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[AtividadeDetalheResposta]:
    try:
        atividade = atividade_service.obter_atividade(sessao, professor, atividade_id)
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    return Resposta(
        mensagem="Atividade encontrada", dados=_dados_atividade(sessao, atividade)
    )


@router.patch("/{atividade_id}")
def atualizar_atividade(
    atividade_id: IdNoCaminho,
    dados: AtividadeAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    enviador: EnviadorPushDep,
    tarefas: BackgroundTasks,
) -> Resposta[AtividadeDetalheResposta]:
    """Altera só os campos enviados. As listas enviadas substituem as atuais.

    Se a atividade já foi liberada e o conteúdo mudou, os alunos recebem um push.
    """
    try:
        atividade, notificacao_id = atividade_service.atualizar_atividade(
            sessao, professor, atividade_id, dados.model_dump(exclude_unset=True)
        )
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    except ERROS_DA_ATIVIDADE as erro:
        raise _traduzir(erro) from None
    if notificacao_id is not None:
        tarefas.add_task(
            notificacao_service.enviar_sem_falhar, sessao, enviador, notificacao_id
        )
    return Resposta(
        mensagem="Atividade atualizada", dados=_dados_atividade(sessao, atividade)
    )


@router.delete("/{atividade_id}")
def excluir_atividade(
    atividade_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[None]:
    """Os arquivos dela e das entregas deixam de abrir em até 5 minutos."""
    try:
        atividade_service.excluir_atividade(sessao, professor, atividade_id)
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    return Resposta(mensagem="Atividade excluída")


@router.get("/{atividade_id}/entregas/{aluno_id}")
def detalhar_entrega(
    atividade_id: IdNoCaminho,
    aluno_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[EntregaResposta]:
    try:
        entrega = atividade_service.obter_entrega(
            sessao, professor, atividade_id, aluno_id
        )
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    except atividade_service.EntregaNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entrega não encontrada"
        ) from None
    return Resposta(mensagem="Entrega encontrada", dados=dados_entrega(sessao, entrega))
