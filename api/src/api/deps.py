"""Dependências reutilizáveis de autenticação e autorização.

Uso em uma rota:

    @router.get("/exemplo")
    def exemplo(usuario: UsuarioAtual): ...

    @router.post("/exemplo")
    def criar(professor: ProfessorAtual): ...

Uso em um router inteiro:

    router = APIRouter(dependencies=[Depends(exigir_tipo(TipoUsuario.PROFESSOR))])
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.database import obter_sessao
from src.core.email import EnviadorEmail, obter_enviador_email
from src.core.security import (
    TokenInvalido,
    decodificar_token,
    decodificar_token_primeiro_acesso,
)
from src.models.usuario import TipoUsuario, Usuario

SessaoDep = Annotated[Session, Depends(obter_sessao)]
EnviadorEmailDep = Annotated[EnviadorEmail, Depends(obter_enviador_email)]

_esquema_bearer = HTTPBearer(auto_error=False)


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


CredenciaisDep = Annotated[
    HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)
]


def _usuario_do_token(
    credenciais: HTTPAuthorizationCredentials | None,
    sessao: Session,
    decodificar: Callable[[str], tuple[int, int]],
) -> Usuario:
    if credenciais is None:
        raise _nao_autenticado()
    try:
        usuario_id, versao_token = decodificar(credenciais.credentials)
    except TokenInvalido:
        raise _nao_autenticado() from None

    usuario = sessao.get(Usuario, usuario_id)
    if (
        usuario is None
        or usuario.deletado_em is not None
        or usuario.versao_token != versao_token
    ):
        raise _nao_autenticado()
    return usuario


def obter_usuario_atual(credenciais: CredenciaisDep, sessao: SessaoDep) -> Usuario:
    return _usuario_do_token(credenciais, sessao, decodificar_token)


def obter_usuario_primeiro_acesso(
    credenciais: CredenciaisDep, sessao: SessaoDep
) -> Usuario:
    """Usuário que validou o código e ainda não concluiu o primeiro acesso."""
    usuario = _usuario_do_token(credenciais, sessao, decodificar_token_primeiro_acesso)
    if usuario.senha is not None:
        raise _nao_autenticado()
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(obter_usuario_atual)]
UsuarioPrimeiroAcesso = Annotated[Usuario, Depends(obter_usuario_primeiro_acesso)]


def exigir_tipo(*tipos: TipoUsuario) -> Callable[[Usuario], Usuario]:
    """Cria uma dependência que só deixa passar usuários dos tipos informados."""

    def verificar(usuario: UsuarioAtual) -> Usuario:
        if usuario.tipo not in tipos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta ação",
            )
        return usuario

    return verificar


ProfessorAtual = Annotated[Usuario, Depends(exigir_tipo(TipoUsuario.PROFESSOR))]
AlunoAtual = Annotated[Usuario, Depends(exigir_tipo(TipoUsuario.ALUNO))]
