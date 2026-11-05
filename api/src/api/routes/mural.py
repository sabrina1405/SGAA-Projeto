from typing import Annotated

from fastapi import APIRouter, Query

from src.api.deps import AlunoAtual, SessaoDep
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.recado import RecadoGeralMuralItem, RecadoMuralItem
from src.schemas.resposta import Resposta
from src.services import recado_service

router = APIRouter(prefix="/mural", tags=["Mural"])


@router.get("/geral")
def listar_recados_gerais(
    _: AlunoAtual, sessao: SessaoDep
) -> Resposta[list[RecadoGeralMuralItem]]:
    """Recados gerais preenchidos, que valem para todos os alunos."""
    itens = recado_service.listar_recados_gerais(sessao)
    return Resposta(
        mensagem="Recados gerais listados",
        dados=[RecadoGeralMuralItem.model_validate(item) for item in itens],
    )


@router.get("")
def listar_mural(
    aluno: AlunoAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[RecadoMuralItem]]:
    """Recados no período de exibição destinados ao aluno: direto, por um grupo
    dele ou para todos."""
    itens, total = recado_service.listar_mural(
        sessao, aluno, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Mural listado",
        dados=Pagina(
            itens=[RecadoMuralItem.model_validate(item) for item in itens],
            total=total,
        ),
    )
