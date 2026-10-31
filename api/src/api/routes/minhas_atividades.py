from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.api.deps import AlunoAtual, SessaoDep
from src.api.routes.atividades import dados_entrega
from src.core.errors import CamposInvalidos
from src.schemas.arquivo import ArquivoResposta
from src.schemas.atividade import (
    EntregaResposta,
    EntregaSalvar,
    MinhaAtividadeDetalhe,
    MinhaAtividadeItem,
    SituacaoMinhaAtividade,
)
from src.schemas.paginacao import (
    PAGINA_MAXIMA,
    TAMANHO_MAXIMO,
    TAMANHO_PADRAO,
    Pagina,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import arquivo_service, atividade_service

router = APIRouter(prefix="/minhas-atividades", tags=["Minhas atividades"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def _atividade_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada"
    )


@router.get("")
def listar_minhas_atividades(
    aluno: AlunoAtual,
    sessao: SessaoDep,
    situacao: SituacaoMinhaAtividade | None = None,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[MinhaAtividadeItem]]:
    """Atividades já liberadas para o aluno. `status` nulo: ainda não entregou."""
    itens, total = atividade_service.listar_minhas_atividades(
        sessao, aluno, situacao=situacao, pagina=pagina, tamanho=tamanho
    )
    return Resposta(
        mensagem="Atividades listadas",
        dados=Pagina(
            itens=[MinhaAtividadeItem.model_validate(item) for item in itens],
            total=total,
        ),
    )


@router.get("/{atividade_id}")
def detalhar_minha_atividade(
    atividade_id: IdNoCaminho, aluno: AlunoAtual, sessao: SessaoDep
) -> Resposta[MinhaAtividadeDetalhe]:
    try:
        atividade, professor_nome, entrega = atividade_service.obter_minha_atividade(
            sessao, aluno, atividade_id
        )
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    anexos = atividade_service.listar_anexos(sessao, atividade)
    return Resposta(
        mensagem="Atividade encontrada",
        dados=MinhaAtividadeDetalhe(
            id=atividade.id,
            titulo=atividade.titulo,
            descricao=atividade.descricao,
            liberar_em=atividade.liberar_em,
            vence_em=atividade.vence_em,
            permite_envio_arquivo=atividade.permite_envio_arquivo,
            professor_nome=professor_nome,
            criado_em=atividade.criado_em,
            anexos=[ArquivoResposta.model_validate(anexo) for anexo in anexos],
            entrega=dados_entrega(sessao, entrega) if entrega is not None else None,
        ),
    )


@router.put("/{atividade_id}/entrega")
def salvar_entrega(
    atividade_id: IdNoCaminho,
    dados: EntregaSalvar,
    aluno: AlunoAtual,
    sessao: SessaoDep,
) -> Resposta[EntregaResposta]:
    """Cria ou edita a resposta. Depois do vencimento, ainda dá para entregar,
    marcada como atrasada, mas não editar."""
    try:
        entrega = atividade_service.salvar_entrega(
            sessao, aluno, atividade_id, **dados.model_dump(exclude_unset=True)
        )
    except atividade_service.AtividadeNaoEncontrada:
        raise _atividade_nao_encontrada() from None
    except atividade_service.EntregaEncerrada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A atividade venceu: a entrega não pode mais ser alterada",
        ) from None
    except atividade_service.AtividadeInvalida as erro:
        raise CamposInvalidos(erro.tipo, erro.mensagem, erro.campos) from None
    except arquivo_service.ArquivosInvalidos as erro:
        ids = ", ".join(str(item_id) for item_id in erro.ids)
        raise CamposInvalidos(
            "arquivo_invalido", f"arquivo inválido: {ids}", ["arquivo_ids"]
        ) from None
    return Resposta(mensagem="Entrega salva", dados=dados_entrega(sessao, entrega))
