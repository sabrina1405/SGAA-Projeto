from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.api.deps import EnviadorPushDep, ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.aula import Aula, StatusAula
from src.schemas.aula import (
    AulaAlunoDetalhe,
    AulaAlunoItem,
    AulaAlunosAdicionar,
    AulaAtualizar,
    AulaCancelar,
    AulaCriar,
    AulaDetalheResposta,
    AulaGrupoItem,
    AulaListaItem,
    Escopo,
    ReposicaoPendenteItem,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import (
    aula_service,
    grupo_service,
    notificacao_service,
    usuario_service,
)

router = APIRouter(prefix="/aulas", tags=["Aulas"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]
IdNaConsulta = Annotated[int | None, Query(ge=1, le=ID_MAXIMO)]
EscopoDep = Annotated[Escopo, Query()]

ERROS_DA_AULA = (
    aula_service.AulaNaoEncontrada,
    aula_service.AulaInvalida,
    aula_service.ConflitoDeHorario,
    aula_service.OperacaoNaoPermitida,
    usuario_service.AlunosInvalidos,
    grupo_service.GruposInvalidos,
)


def _aula_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada"
    )


def _traduzir(erro: Exception) -> Exception:
    """Converte o erro do service na resposta HTTP correspondente."""
    if isinstance(erro, aula_service.AulaNaoEncontrada):
        return _aula_nao_encontrada()
    if isinstance(erro, aula_service.AulaInvalida):
        return CamposInvalidos(erro.tipo, erro.mensagem, erro.campos)
    if isinstance(erro, aula_service.ConflitoDeHorario):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f'Conflito com a aula "{erro.aula.titulo}" de '
                f"{aula_service.formatar_horario(erro.aula.inicio)}"
            ),
        )
    if isinstance(erro, aula_service.OperacaoNaoPermitida):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=erro.mensagem)
    ids = ", ".join(str(item_id) for item_id in erro.ids)
    if isinstance(erro, usuario_service.AlunosInvalidos):
        return CamposInvalidos(
            "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_ids"]
        )
    return CamposInvalidos(
        "grupo_invalido", f"grupo não encontrado: {ids}", ["grupo_ids"]
    )


def _dados_aula(sessao: Session, aula: Aula) -> AulaDetalheResposta:
    alunos = aula_service.listar_alunos_da_aula(sessao, aula)
    grupos = aula_service.listar_grupos_da_aula(sessao, aula)
    return AulaDetalheResposta(
        id=aula.id,
        titulo=aula.titulo,
        descricao=aula.descricao,
        anotacoes=aula.anotacoes,
        inicio=aula.inicio,
        fim=aula.fim,
        status=aula.status,
        motivo_cancelamento=aula.motivo_cancelamento,
        serie_id=aula.serie_id,
        reposicao_de_aula_id=aula.reposicao_de_aula_id,
        alunos=[AulaAlunoDetalhe.model_validate(aluno) for aluno in alunos],
        grupos=[AulaGrupoItem.model_validate(grupo) for grupo in grupos],
        criado_em=aula.criado_em,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_aula(
    dados: AulaCriar, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[AulaDetalheResposta]:
    """Com `repetir_semanalmente`, cria uma aula por semana até `repetir_ate` e
    devolve a primeira. Os alunos recebem lembretes 1 semana, 1 dia e 30 minutos
    antes de cada aula."""
    try:
        aula = aula_service.criar_aula(sessao, professor, **dados.model_dump())
    except ERROS_DA_AULA as erro:
        raise _traduzir(erro) from None
    return Resposta(mensagem="Aula criada", dados=_dados_aula(sessao, aula))


@router.get("")
def listar_aulas(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    data_inicio: date,
    data_fim: date,
    status_aula: Annotated[StatusAula | None, Query(alias="status")] = None,
    aluno_id: IdNaConsulta = None,
    grupo_id: IdNaConsulta = None,
) -> Resposta[list[AulaListaItem]]:
    """Aulas que começam entre `data_inicio` e `data_fim` (até 62 dias), em ordem
    de início, com os alunos de cada uma."""
    try:
        aulas = aula_service.listar_aulas(
            sessao,
            professor,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status_aula,
            aluno_id=aluno_id,
            grupo_id=grupo_id,
        )
    except aula_service.AulaInvalida as erro:
        raise CamposInvalidos(erro.tipo, erro.mensagem, erro.campos, "query") from None
    alunos = aula_service.alunos_das_aulas(sessao, [aula.id for aula in aulas])
    return Resposta(
        mensagem="Aulas listadas",
        dados=[
            AulaListaItem(
                id=aula.id,
                titulo=aula.titulo,
                inicio=aula.inicio,
                fim=aula.fim,
                status=aula.status,
                serie_id=aula.serie_id,
                alunos=[
                    AulaAlunoItem.model_validate(aluno)
                    for aluno in alunos.get(aula.id, [])
                ],
            )
            for aula in aulas
        ],
    )


# As rotas de reposição vêm antes de /{aula_id}.


@router.get("/reposicoes-pendentes")
def listar_reposicoes_pendentes(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[ReposicaoPendenteItem]]:
    """Alunos que ficaram sem aula e ainda não têm reposição marcada."""
    itens, total = aula_service.listar_reposicoes_pendentes(
        sessao, professor, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Reposições pendentes listadas",
        dados=Pagina(
            itens=[ReposicaoPendenteItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.delete("/reposicoes-pendentes/{aula_id}/{aluno_id}")
def dispensar_reposicao(
    aula_id: IdNoCaminho,
    aluno_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[None]:
    """Tira a pendência sem marcar aula."""
    try:
        aula_service.dispensar_reposicao(sessao, professor, aula_id, aluno_id)
    except aula_service.ReposicaoNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reposição pendente não encontrada",
        ) from None
    return Resposta(mensagem="Reposição dispensada")


@router.get("/{aula_id}")
def detalhar_aula(
    aula_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[AulaDetalheResposta]:
    try:
        aula = aula_service.obter_aula(sessao, professor, aula_id)
    except aula_service.AulaNaoEncontrada:
        raise _aula_nao_encontrada() from None
    return Resposta(mensagem="Aula encontrada", dados=_dados_aula(sessao, aula))


@router.patch("/{aula_id}")
def atualizar_aula(
    aula_id: IdNoCaminho,
    dados: AulaAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    escopo: EscopoDep = Escopo.ESTA,
) -> Resposta[AulaDetalheResposta]:
    """Altera só os campos enviados. Com `escopo=esta_e_seguintes`, altera também
    as próximas aulas agendadas da série; a mudança de horário as desloca pelo
    mesmo tanto."""
    try:
        aula = aula_service.atualizar_aula(
            sessao, professor, aula_id, dados.model_dump(exclude_unset=True), escopo
        )
    except ERROS_DA_AULA as erro:
        raise _traduzir(erro) from None
    return Resposta(mensagem="Aula atualizada", dados=_dados_aula(sessao, aula))


@router.post("/{aula_id}/cancelar")
def cancelar_aula(
    aula_id: IdNoCaminho,
    dados: AulaCancelar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    enviador: EnviadorPushDep,
    tarefas: BackgroundTasks,
    escopo: EscopoDep = Escopo.ESTA,
) -> Resposta[AulaDetalheResposta]:
    """Os alunos recebem um push. Com `repor`, cada aluno fica com uma reposição
    pendente."""
    try:
        aula, notificacao_id = aula_service.cancelar_aula(
            sessao, professor, aula_id, escopo, **dados.model_dump()
        )
    except ERROS_DA_AULA as erro:
        raise _traduzir(erro) from None
    if notificacao_id is not None:
        tarefas.add_task(
            notificacao_service.enviar_sem_falhar, sessao, enviador, notificacao_id
        )
    return Resposta(mensagem="Aula cancelada", dados=_dados_aula(sessao, aula))


@router.post("/{aula_id}/alunos")
def adicionar_alunos(
    aula_id: IdNoCaminho,
    dados: AulaAlunosAdicionar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    escopo: EscopoDep = Escopo.ESTA,
) -> Resposta[AulaDetalheResposta]:
    """Quem já está na aula é ignorado."""
    try:
        aula = aula_service.adicionar_alunos(
            sessao, professor, aula_id, escopo, **dados.model_dump()
        )
    except ERROS_DA_AULA as erro:
        raise _traduzir(erro) from None
    return Resposta(mensagem="Alunos adicionados", dados=_dados_aula(sessao, aula))


@router.delete("/{aula_id}/alunos/{aluno_id}")
def remover_aluno(
    aula_id: IdNoCaminho,
    aluno_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    escopo: EscopoDep = Escopo.ESTA,
) -> Resposta[None]:
    try:
        aula_service.remover_aluno(sessao, professor, aula_id, aluno_id, escopo)
    except aula_service.AlunoForaDaAula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não está na aula",
        ) from None
    except ERROS_DA_AULA as erro:
        raise _traduzir(erro) from None
    return Resposta(mensagem="Aluno removido da aula")
