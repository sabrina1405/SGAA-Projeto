from typing import Annotated

from fastapi import APIRouter, Path

from src.api.deps import SessaoDep, UsuarioAtual
from src.schemas.dispositivo import DispositivoRegistrar
from src.schemas.resposta import Resposta
from src.services import dispositivo_service

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos"])


@router.post("")
def registrar_dispositivo(
    dados: DispositivoRegistrar, usuario: UsuarioAtual, sessao: SessaoDep
) -> Resposta[None]:
    """Registra o ExpoPushToken do aparelho, depois do login."""
    dispositivo_service.registrar_dispositivo(
        sessao, usuario, dados.token, dados.plataforma
    )
    return Resposta(mensagem="Dispositivo registrado")


@router.delete("/{token}")
def remover_dispositivo(
    token: Annotated[str, Path(max_length=255)],
    usuario: UsuarioAtual,
    sessao: SessaoDep,
) -> Resposta[None]:
    """Para de enviar push ao aparelho, no logout. Repetir a chamada não é erro."""
    dispositivo_service.remover_dispositivo(sessao, usuario, token)
    return Resposta(mensagem="Dispositivo removido")
