from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from src.api.deps import EnviadorEmailDep, EnviadorPushDep, ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.schemas.aluno import hoje
from src.schemas.financeiro import (
    CobrancaAtualizar,
    CobrancaCriar,
    CobrancaPagar,
    CobrancaResposta,
    PlanoAtualizar,
    PlanoCriar,
    PlanoResposta,
    ResumoResposta,
    Situacao,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import financeiro_service, notificacao_service, usuario_service

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]
IdNaConsulta = Annotated[int | None, Query(ge=1, le=ID_MAXIMO)]
PaginaDep = Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)]
TamanhoDep = Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)]


def _aluno_invalido(erro: usuario_service.AlunosInvalidos) -> CamposInvalidos:
    ids = ", ".join(str(item_id) for item_id in erro.ids)
    return CamposInvalidos(
        "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_id"]
    )


class Avisos:
    """Envia na hora o aviso de criação ou edição, por push e e-mail."""

    def __init__(
        self,
        tarefas: BackgroundTasks,
        sessao: SessaoDep,
        enviador_push: EnviadorPushDep,
        enviador_email: EnviadorEmailDep,
    ) -> None:
        self.tarefas = tarefas
        self.sessao = sessao
        self.enviador_push = enviador_push
        self.enviador_email = enviador_email

    def enviar(self, notificacao_id: int) -> None:
        self.tarefas.add_task(
            notificacao_service.enviar_sem_falhar,
            self.sessao,
            self.enviador_push,
            notificacao_id,
            self.enviador_email,
        )


AvisosDep = Annotated[Avisos, Depends()]


def _nao_encontrado(detalhe: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detalhe)


def _transicao_invalida(detalhe: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalhe)


# --- planos ---


@router.post("/planos", status_code=status.HTTP_201_CREATED)
def criar_plano(
    dados: PlanoCriar, professor: ProfessorAtual, sessao: SessaoDep, avisos: AvisosDep
) -> Resposta[PlanoResposta]:
    """Cobrança recorrente de um aluno. As cobranças que vencem nos próximos
    35 dias já são geradas; as seguintes saem pela tarefa agendada. O aluno é
    avisado na hora, pelo app e por e-mail."""
    if dados.inicio < hoje():
        raise CamposInvalidos(
            "inicio_no_passado",
            "o início não pode estar no passado; lance as anteriores como avulsas",
            ["inicio"],
        )
    try:
        plano, aviso_id = financeiro_service.criar_plano(
            sessao, professor, **dados.model_dump()
        )
    except usuario_service.AlunosInvalidos as erro:
        raise _aluno_invalido(erro) from None
    avisos.enviar(aviso_id)
    return Resposta(
        mensagem="Plano criado",
        dados=PlanoResposta.model_validate(
            financeiro_service.dados_plano(sessao, plano)
        ),
    )


@router.get("/planos")
def listar_planos(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    aluno_id: IdNaConsulta = None,
    pagina: PaginaDep = 1,
    tamanho: TamanhoDep = TAMANHO_PADRAO,
) -> Resposta[Pagina[PlanoResposta]]:
    """Planos ativos, pelo nome do aluno."""
    itens, total = financeiro_service.listar_planos(
        sessao, professor, aluno_id=aluno_id, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Planos listados",
        dados=Pagina(
            itens=[PlanoResposta.model_validate(item) for item in itens], total=total
        ),
    )


@router.get("/planos/{plano_id}")
def detalhar_plano(
    plano_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[PlanoResposta]:
    try:
        plano = financeiro_service.obter_plano(sessao, professor, plano_id)
    except financeiro_service.PlanoNaoEncontrado:
        raise _nao_encontrado("Plano não encontrado") from None
    return Resposta(
        mensagem="Plano encontrado",
        dados=PlanoResposta.model_validate(
            financeiro_service.dados_plano(sessao, plano)
        ),
    )


@router.patch("/planos/{plano_id}")
def atualizar_plano(
    plano_id: IdNoCaminho,
    dados: PlanoAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    avisos: AvisosDep,
) -> Resposta[PlanoResposta]:
    """Altera só os campos enviados. As cobranças ainda não vencidas seguem a
    mudança; as vencidas e as pagas ficam como estão. O aluno é avisado."""
    try:
        plano, aviso_id = financeiro_service.atualizar_plano(
            sessao, professor, plano_id, dados.model_dump(exclude_unset=True)
        )
    except financeiro_service.PlanoNaoEncontrado:
        raise _nao_encontrado("Plano não encontrado") from None
    except ValueError as erro:
        raise CamposInvalidos("plano_invalido", str(erro), ["body"]) from None
    avisos.enviar(aviso_id)
    return Resposta(
        mensagem="Plano atualizado",
        dados=PlanoResposta.model_validate(
            financeiro_service.dados_plano(sessao, plano)
        ),
    )


@router.delete("/planos/{plano_id}")
def encerrar_plano(
    plano_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[None]:
    """As cobranças ainda não vencidas são canceladas; as vencidas seguem devidas."""
    try:
        financeiro_service.encerrar_plano(sessao, professor, plano_id)
    except financeiro_service.PlanoNaoEncontrado:
        raise _nao_encontrado("Plano não encontrado") from None
    return Resposta(mensagem="Plano encerrado")


# --- cobranças ---


def _resposta_cobranca(sessao, cobranca, mensagem: str) -> Resposta[CobrancaResposta]:
    return Resposta(
        mensagem=mensagem,
        dados=CobrancaResposta.model_validate(
            financeiro_service.dados_cobranca(sessao, cobranca)
        ),
    )


@router.post("/cobrancas", status_code=status.HTTP_201_CREATED)
def criar_cobranca(
    dados: CobrancaCriar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    avisos: AvisosDep,
) -> Resposta[CobrancaResposta]:
    """Cobrança avulsa. O aluno é avisado na hora, pelo app e por e-mail."""
    try:
        cobranca, aviso_id = financeiro_service.criar_cobranca(
            sessao, professor, **dados.model_dump()
        )
    except usuario_service.AlunosInvalidos as erro:
        raise _aluno_invalido(erro) from None
    avisos.enviar(aviso_id)
    return _resposta_cobranca(sessao, cobranca, "Cobrança criada")


@router.get("/cobrancas")
def listar_cobrancas(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    aluno_id: IdNaConsulta = None,
    situacao: Situacao | None = None,
    de: date | None = None,
    ate: date | None = None,
    pagina: PaginaDep = 1,
    tamanho: TamanhoDep = TAMANHO_PADRAO,
) -> Resposta[Pagina[CobrancaResposta]]:
    """Por vencimento, da mais antiga à mais nova."""
    itens, total = financeiro_service.listar_cobrancas(
        sessao,
        professor,
        aluno_id=aluno_id,
        situacao_filtro=situacao.value if situacao else None,
        de=de,
        ate=ate,
        pagina=pagina,
        tamanho=tamanho,
    )
    return Resposta(
        mensagem="Cobranças listadas",
        dados=Pagina(
            itens=[CobrancaResposta.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/cobrancas/{cobranca_id}")
def detalhar_cobranca(
    cobranca_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[CobrancaResposta]:
    try:
        cobranca = financeiro_service.obter_cobranca(sessao, professor, cobranca_id)
    except financeiro_service.CobrancaNaoEncontrada:
        raise _nao_encontrado("Cobrança não encontrada") from None
    return _resposta_cobranca(sessao, cobranca, "Cobrança encontrada")


@router.patch("/cobrancas/{cobranca_id}")
def atualizar_cobranca(
    cobranca_id: IdNoCaminho,
    dados: CobrancaAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    avisos: AvisosDep,
) -> Resposta[CobrancaResposta]:
    """Só para cobranças pendentes, inclusive as vencidas. O aluno é avisado."""
    try:
        cobranca, aviso_id = financeiro_service.atualizar_cobranca(
            sessao, professor, cobranca_id, dados.model_dump(exclude_unset=True)
        )
    except financeiro_service.CobrancaNaoEncontrada:
        raise _nao_encontrado("Cobrança não encontrada") from None
    except financeiro_service.TransicaoInvalida:
        raise _transicao_invalida("Só cobranças pendentes podem ser editadas") from None
    except financeiro_service.VencimentoDuplicado:
        raise _transicao_invalida(
            "O plano já tem uma cobrança com esse vencimento"
        ) from None
    avisos.enviar(aviso_id)
    return _resposta_cobranca(sessao, cobranca, "Cobrança atualizada")


@router.post("/cobrancas/{cobranca_id}/pagar")
def pagar_cobranca(
    cobranca_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
    dados: CobrancaPagar | None = None,
) -> Resposta[CobrancaResposta]:
    """Dá baixa no pagamento recebido por Pix. Sem corpo, vale o momento atual."""
    try:
        cobranca = financeiro_service.pagar(
            sessao, professor, cobranca_id, dados.paga_em if dados else None
        )
    except financeiro_service.CobrancaNaoEncontrada:
        raise _nao_encontrado("Cobrança não encontrada") from None
    except financeiro_service.TransicaoInvalida:
        raise _transicao_invalida("Só cobranças pendentes podem ser pagas") from None
    return _resposta_cobranca(sessao, cobranca, "Pagamento registrado")


@router.post("/cobrancas/{cobranca_id}/reabrir")
def reabrir_cobranca(
    cobranca_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[CobrancaResposta]:
    """Desfaz a baixa de uma cobrança paga."""
    try:
        cobranca = financeiro_service.reabrir(sessao, professor, cobranca_id)
    except financeiro_service.CobrancaNaoEncontrada:
        raise _nao_encontrado("Cobrança não encontrada") from None
    except financeiro_service.TransicaoInvalida:
        raise _transicao_invalida("Só cobranças pagas podem ser reabertas") from None
    return _resposta_cobranca(sessao, cobranca, "Pagamento desfeito")


@router.post("/cobrancas/{cobranca_id}/cancelar")
def cancelar_cobranca(
    cobranca_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[CobrancaResposta]:
    try:
        cobranca = financeiro_service.cancelar(sessao, professor, cobranca_id)
    except financeiro_service.CobrancaNaoEncontrada:
        raise _nao_encontrado("Cobrança não encontrada") from None
    except financeiro_service.TransicaoInvalida:
        raise _transicao_invalida(
            "Só cobranças pendentes podem ser canceladas"
        ) from None
    return _resposta_cobranca(sessao, cobranca, "Cobrança cancelada")


@router.get("/resumo")
def resumo(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    mes: Annotated[str | None, Query(pattern=r"^[1-9]\d{3}-(0[1-9]|1[0-2])$")] = None,
) -> Resposta[ResumoResposta]:
    """Totais do mês (`AAAA-MM`, padrão: o atual) pelo vencimento, em centavos."""
    referencia = mes or hoje().strftime("%Y-%m")
    ano, numero = (int(parte) for parte in referencia.split("-"))
    totais = financeiro_service.resumo_do_mes(sessao, professor, ano, numero)
    return Resposta(
        mensagem="Resumo do mês", dados=ResumoResposta(mes=referencia, **totais)
    )
