from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, status

from src.api.deps import DriveDep, SessaoDep, UsuarioAtual
from src.core.config import obter_config
from src.core.drive import FalhaDrive
from src.core.errors import CamposInvalidos
from src.schemas.arquivo import (
    ArquivoConfirmar,
    ArquivoResposta,
    ArquivoSessaoCriar,
    ArquivoSessaoResposta,
)
from src.schemas.resposta import Resposta
from src.schemas.tipos import ID_MAXIMO
from src.services import arquivo_service

router = APIRouter(prefix="/arquivos", tags=["Arquivos"])

IdNoCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


def _drive_indisponivel() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Serviço de arquivos indisponível. Tente novamente em instantes.",
    )


def _arquivo_nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado"
    )


@router.post("/sessao", status_code=status.HTTP_201_CREATED)
def abrir_sessao(
    dados: ArquivoSessaoCriar,
    usuario: UsuarioAtual,
    sessao: SessaoDep,
    drive: DriveDep,
    origem: Annotated[str | None, Header(alias="origin")] = None,
) -> Resposta[ArquivoSessaoResposta]:
    """Primeiro passo do envio: o app manda o arquivo direto a `url_upload` e
    depois chama a confirmação. Até 5 MB."""
    # Só as origens conhecidas: é o que libera o navegador a usar a URL da sessão.
    origem_permitida = origem if origem in obter_config().lista_cors_origins else None
    try:
        arquivo, url = arquivo_service.abrir_sessao(
            sessao, usuario, drive, **dados.model_dump(), origem=origem_permitida
        )
    except arquivo_service.ArquivoInvalido as erro:
        raise CamposInvalidos(erro.tipo, erro.mensagem, erro.campos) from None
    except arquivo_service.LimiteDeArquivos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Muitos arquivos enviados e ainda não salvos. Tente mais tarde.",
        ) from None
    except FalhaDrive:
        raise _drive_indisponivel() from None
    return Resposta(
        mensagem="Sessão de envio aberta",
        dados=ArquivoSessaoResposta(arquivo_id=arquivo.id, url_upload=url),
    )


@router.post("/{arquivo_id}/confirmar")
def confirmar(
    arquivo_id: IdNoCaminho,
    dados: ArquivoConfirmar,
    usuario: UsuarioAtual,
    sessao: SessaoDep,
    drive: DriveDep,
) -> Resposta[ArquivoResposta]:
    """Confere no Drive o que foi enviado e cria o link. Pode ser repetida."""
    try:
        arquivo = arquivo_service.confirmar(
            sessao, usuario, drive, arquivo_id, dados.drive_file_id
        )
    except arquivo_service.ArquivoNaoEncontrado:
        raise _arquivo_nao_encontrado() from None
    except arquivo_service.ArquivoInvalido as erro:
        raise CamposInvalidos(erro.tipo, erro.mensagem, erro.campos) from None
    except FalhaDrive:
        raise _drive_indisponivel() from None
    return Resposta(
        mensagem="Arquivo confirmado", dados=ArquivoResposta.model_validate(arquivo)
    )


@router.delete("/{arquivo_id}")
def descartar(
    arquivo_id: IdNoCaminho, usuario: UsuarioAtual, sessao: SessaoDep
) -> Resposta[None]:
    """Desiste de um arquivo que ainda não foi salvo em uma atividade ou entrega."""
    try:
        arquivo_service.descartar(sessao, usuario, arquivo_id)
    except arquivo_service.ArquivoNaoEncontrado:
        raise _arquivo_nao_encontrado() from None
    except arquivo_service.ArquivoEmUso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O arquivo está em uso. Remova-o pela atividade ou entrega.",
        ) from None
    return Resposta(mensagem="Arquivo descartado")
