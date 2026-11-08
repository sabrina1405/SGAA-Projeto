from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.api.deps import ProfessorAtual, SessaoDep
from src.core.errors import CamposInvalidos
from src.models.material import Pasta
from src.schemas.aluno import AlunoListaItem
from src.schemas.arquivo import ArquivoResposta
from src.schemas.material import (
    ArquivoDaPastaMover,
    ArquivosDaPastaAdicionar,
    PastaAtualizar,
    PastaCaminhoItem,
    PastaCriar,
    PastaDetalheResposta,
    PastaListaItem,
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
    grupo_service,
    material_service,
    usuario_service,
)

router = APIRouter(prefix="/pastas", tags=["Pastas"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def dados_pasta(sessao: Session, pasta: Pasta) -> PastaDetalheResposta:
    raiz = material_service.obter_raiz(sessao, pasta)
    alunos = material_service.listar_alunos_da_pasta(sessao, raiz.id)
    grupos = material_service.listar_grupos_da_pasta(sessao, raiz.id)
    return PastaDetalheResposta(
        id=pasta.id,
        nome=pasta.nome,
        pasta_pai_id=pasta.pasta_pai_id,
        raiz_id=raiz.id,
        caminho=[
            PastaCaminhoItem.model_validate(item)
            for item in material_service.caminho(sessao, pasta)
        ],
        todos_alunos=raiz.todos_alunos,
        todos_grupos=raiz.todos_grupos,
        alunos=[AlunoListaItem.model_validate(aluno) for aluno in alunos],
        grupos=[RecadoGrupoItem.model_validate(grupo) for grupo in grupos],
        subpastas=[
            PastaListaItem.model_validate(item)
            for item in material_service.listar_subpastas(sessao, pasta)
        ],
        arquivos=[
            ArquivoResposta.model_validate(arquivo)
            for arquivo in material_service.listar_arquivos(sessao, pasta)
        ],
        criado_em=pasta.criado_em,
    )


def _pasta_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Pasta não encontrada"
    )


def _nome_repetido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe uma pasta com esse nome neste lugar",
    )


ERROS_DE_CAMPO = (
    material_service.PastaInvalida,
    grupo_service.GruposInvalidos,
    usuario_service.AlunosInvalidos,
    arquivo_service.ArquivosInvalidos,
)


def _campos_invalidos(erro: Exception) -> CamposInvalidos:
    if isinstance(erro, material_service.PastaInvalida):
        return CamposInvalidos(erro.tipo, erro.mensagem, erro.campos)
    ids = ", ".join(str(item_id) for item_id in erro.ids)
    if isinstance(erro, usuario_service.AlunosInvalidos):
        return CamposInvalidos(
            "aluno_invalido", f"aluno não encontrado: {ids}", ["aluno_ids"]
        )
    if isinstance(erro, arquivo_service.ArquivosInvalidos):
        return CamposInvalidos(
            "arquivo_invalido", f"arquivo inválido: {ids}", ["arquivo_ids"]
        )
    return CamposInvalidos(
        "grupo_invalido", f"grupo não encontrado: {ids}", ["grupo_ids"]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_pasta(
    dados: PastaCriar, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[PastaDetalheResposta]:
    """Sem `pasta_pai_id`, cria uma pasta raiz. Os destinatários só são aceitos
    na raiz e valem para todas as subpastas."""
    try:
        pasta = material_service.criar_pasta(sessao, professor, **dados.model_dump())
    except material_service.NomeDePastaRepetido:
        raise _nome_repetido() from None
    except ERROS_DE_CAMPO as erro:
        raise _campos_invalidos(erro) from None
    return Resposta(mensagem="Pasta criada", dados=dados_pasta(sessao, pasta))


@router.get("")
def listar_pastas(
    professor: ProfessorAtual,
    sessao: SessaoDep,
    pasta_pai_id: Annotated[int | None, Query(ge=1, le=ID_MAXIMO)] = None,
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=TAMANHO_MAXIMO)] = TAMANHO_PADRAO,
) -> Resposta[Pagina[PastaListaItem]]:
    """Pastas raiz, ou as subpastas de `pasta_pai_id`, em ordem alfabética."""
    try:
        itens, total = material_service.listar_pastas(
            sessao, professor, pasta_pai_id=pasta_pai_id, pagina=pagina, tamanho=tamanho
        )
    except material_service.PastaNaoEncontrada:
        raise _pasta_nao_encontrada() from None
    return Resposta(
        mensagem="Pastas listadas",
        dados=Pagina(
            itens=[PastaListaItem.model_validate(item) for item in itens], total=total
        ),
    )


@router.get("/{pasta_id}")
def detalhar_pasta(
    pasta_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[PastaDetalheResposta]:
    try:
        pasta = material_service.obter_pasta(sessao, professor, pasta_id)
    except material_service.PastaNaoEncontrada:
        raise _pasta_nao_encontrada() from None
    return Resposta(mensagem="Pasta encontrada", dados=dados_pasta(sessao, pasta))


@router.patch("/{pasta_id}")
def atualizar_pasta(
    pasta_id: IdNoCaminho,
    dados: PastaAtualizar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[PastaDetalheResposta]:
    """Altera só os campos enviados. `pasta_pai_id` move a pasta, e nulo a leva
    para a raiz. Uma raiz que vira subpasta passa a seguir os destinatários da
    nova raiz."""
    try:
        pasta = material_service.atualizar_pasta(
            sessao, professor, pasta_id, dados.model_dump(exclude_unset=True)
        )
    except material_service.PastaNaoEncontrada:
        raise _pasta_nao_encontrada() from None
    except material_service.NomeDePastaRepetido:
        raise _nome_repetido() from None
    except ERROS_DE_CAMPO as erro:
        raise _campos_invalidos(erro) from None
    return Resposta(mensagem="Pasta atualizada", dados=dados_pasta(sessao, pasta))


@router.delete("/{pasta_id}")
def excluir_pasta(
    pasta_id: IdNoCaminho, professor: ProfessorAtual, sessao: SessaoDep
) -> Resposta[None]:
    """Exclui também as subpastas e os materiais delas."""
    try:
        material_service.excluir_pasta(sessao, professor, pasta_id)
    except material_service.PastaNaoEncontrada:
        raise _pasta_nao_encontrada() from None
    return Resposta(mensagem="Pasta excluída")


@router.post("/{pasta_id}/arquivos")
def adicionar_arquivos(
    pasta_id: IdNoCaminho,
    dados: ArquivosDaPastaAdicionar,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[PastaDetalheResposta]:
    """Guarda na pasta arquivos já enviados e confirmados em /arquivos."""
    try:
        pasta = material_service.adicionar_arquivos(
            sessao, professor, pasta_id, dados.arquivo_ids
        )
    except material_service.PastaNaoEncontrada:
        raise _pasta_nao_encontrada() from None
    except ERROS_DE_CAMPO as erro:
        raise _campos_invalidos(erro) from None
    return Resposta(mensagem="Materiais adicionados", dados=dados_pasta(sessao, pasta))


@router.patch("/{pasta_id}/arquivos/{arquivo_id}")
def mover_arquivo(
    pasta_id: IdNoCaminho,
    arquivo_id: IdNoCaminho,
    dados: ArquivoDaPastaMover,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[PastaDetalheResposta]:
    """Leva o material para outra pasta do professor. Devolve a pasta de destino."""
    try:
        destino = material_service.mover_arquivo(
            sessao, professor, pasta_id, arquivo_id, dados.pasta_id
        )
    except (
        material_service.PastaNaoEncontrada,
        material_service.ArquivoForaDaPasta,
    ):
        raise _pasta_nao_encontrada() from None
    except ERROS_DE_CAMPO as erro:
        raise _campos_invalidos(erro) from None
    return Resposta(mensagem="Material movido", dados=dados_pasta(sessao, destino))


@router.delete("/{pasta_id}/arquivos/{arquivo_id}")
def remover_arquivo(
    pasta_id: IdNoCaminho,
    arquivo_id: IdNoCaminho,
    professor: ProfessorAtual,
    sessao: SessaoDep,
) -> Resposta[None]:
    """Tira o material da pasta e o apaga do Drive."""
    try:
        material_service.remover_arquivo(sessao, professor, pasta_id, arquivo_id)
    except (
        material_service.PastaNaoEncontrada,
        material_service.ArquivoForaDaPasta,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não encontrado nesta pasta",
        ) from None
    return Resposta(mensagem="Material removido")
