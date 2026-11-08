from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.api.deps import AlunoAtual, SessaoDep
from src.schemas.arquivo import ArquivoResposta
from src.schemas.material import (
    MaterialDetalheResposta,
    MaterialListaItem,
    PastaCaminhoItem,
    PastaListaItem,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import material_service

router = APIRouter(prefix="/meus-materiais", tags=["Meus materiais"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


@router.get("")
def listar_materiais(
    aluno: AlunoAtual,
    sessao: SessaoDep,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[MaterialListaItem]]:
    """Pastas raiz que os professores liberaram ao aluno."""
    itens, total = material_service.listar_materiais(
        sessao, aluno, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Materiais listados",
        dados=Pagina(
            itens=[MaterialListaItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/{pasta_id}")
def detalhar_material(
    pasta_id: IdNoCaminho, aluno: AlunoAtual, sessao: SessaoDep
) -> Resposta[MaterialDetalheResposta]:
    """Subpastas e materiais de uma pasta liberada ao aluno."""
    try:
        pasta, professor_nome = material_service.obter_material(sessao, aluno, pasta_id)
    except material_service.PastaNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada"
        ) from None
    return Resposta(
        mensagem="Pasta encontrada",
        dados=MaterialDetalheResposta(
            id=pasta.id,
            nome=pasta.nome,
            professor_nome=professor_nome,
            caminho=[
                PastaCaminhoItem.model_validate(item)
                for item in material_service.caminho(sessao, pasta)
            ],
            subpastas=[
                PastaListaItem.model_validate(item)
                for item in material_service.listar_subpastas(sessao, pasta)
            ],
            arquivos=[
                ArquivoResposta.model_validate(arquivo)
                for arquivo in material_service.listar_arquivos(sessao, pasta)
            ],
        ),
    )
