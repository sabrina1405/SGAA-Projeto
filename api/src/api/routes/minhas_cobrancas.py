from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.api.deps import AlunoAtual, SessaoDep
from src.schemas.financeiro import MinhaCobrancaResposta, Situacao
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import financeiro_service

router = APIRouter(prefix="/minhas-cobrancas", tags=["Minhas cobranças"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


@router.get("")
def listar_minhas_cobrancas(
    aluno: AlunoAtual,
    sessao: SessaoDep,
    situacao: Situacao | None = None,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[MinhaCobrancaResposta]]:
    """Cobranças de todas as professoras, da mais recente à mais antiga, com a
    chave Pix de quem cobra."""
    itens, total = financeiro_service.listar_minhas_cobrancas(
        sessao,
        aluno,
        situacao_filtro=situacao.value if situacao else None,
        pagina=pagina,
        tamanho=tamanho,
    )
    return Resposta(
        mensagem="Cobranças listadas",
        dados=Pagina(
            itens=[MinhaCobrancaResposta.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/{cobranca_id}")
def detalhar_minha_cobranca(
    cobranca_id: IdNoCaminho, aluno: AlunoAtual, sessao: SessaoDep
) -> Resposta[MinhaCobrancaResposta]:
    try:
        linha = financeiro_service.obter_minha_cobranca(sessao, aluno, cobranca_id)
    except financeiro_service.CobrancaNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada"
        ) from None
    return Resposta(
        mensagem="Cobrança encontrada",
        dados=MinhaCobrancaResposta.model_validate(linha),
    )
