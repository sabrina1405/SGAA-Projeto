from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query, status

from src.api.deps import AlunoAtual, EnviadorPushDep, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.aula import StatusAula
from src.schemas.aula import AgendaItem, ParticipacaoCancelar
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import aula_service, notificacao_service

router = APIRouter(prefix="/agenda", tags=["Agenda"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def _aula_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada"
    )


@router.get("")
def listar_agenda(
    aluno: AlunoAtual,
    sessao: SessaoDep,
    data_inicio: date,
    data_fim: date,
    status_aula: Annotated[StatusAula | None, Query(alias="status")] = None,
) -> Resposta[list[AgendaItem]]:
    """Aulas do aluno que começam entre `data_inicio` e `data_fim` (até 62 dias),
    inclusive as que ele cancelou."""
    try:
        itens = aula_service.listar_agenda(
            sessao,
            aluno,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status_aula,
        )
    except aula_service.AulaInvalida as erro:
        raise CamposInvalidos(erro.tipo, erro.mensagem, erro.campos, "query") from None
    return Resposta(
        mensagem="Agenda listada",
        dados=[AgendaItem.model_validate(item) for item in itens],
    )


@router.get("/{aula_id}")
def detalhar_aula(
    aula_id: IdNoCaminho, aluno: AlunoAtual, sessao: SessaoDep
) -> Resposta[AgendaItem]:
    try:
        item = aula_service.obter_da_agenda(sessao, aluno, aula_id)
    except aula_service.AulaNaoEncontrada:
        raise _aula_nao_encontrada() from None
    return Resposta(mensagem="Aula encontrada", dados=AgendaItem.model_validate(item))


@router.post("/{aula_id}/cancelar")
def cancelar_participacao(
    aula_id: IdNoCaminho,
    dados: ParticipacaoCancelar,
    aluno: AlunoAtual,
    sessao: SessaoDep,
    enviador: EnviadorPushDep,
    tarefas: BackgroundTasks,
) -> Resposta[AgendaItem]:
    """O aluno sai da aula e o professor recebe um push para marcar a reposição."""
    try:
        item, notificacao_id = aula_service.cancelar_participacao(
            sessao, aluno, aula_id, dados.motivo
        )
    except aula_service.AulaNaoEncontrada:
        raise _aula_nao_encontrada() from None
    except aula_service.OperacaoNaoPermitida as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=erro.mensagem
        ) from None
    tarefas.add_task(
        notificacao_service.enviar_sem_falhar, sessao, enviador, notificacao_id
    )
    return Resposta(mensagem="Aula cancelada", dados=AgendaItem.model_validate(item))
