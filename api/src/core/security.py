import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from src.core.config import obter_config

ALGORITMO_JWT = "HS256"
ESCOPO_PRIMEIRO_ACESSO = "primeiro_acesso"
# Tempo para o usuário preencher o formulário depois de validar o código.
VALIDADE_TOKEN_PRIMEIRO_ACESSO = timedelta(minutes=30)

_hasher = PasswordHasher()


class TokenInvalido(Exception):
    pass


def agora() -> datetime:
    return datetime.now(UTC)


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    try:
        return _hasher.verify(hash_salvo, senha)
    except (VerificationError, InvalidHashError):
        return False


def precisa_rehash(hash_salvo: str) -> bool:
    return _hasher.check_needs_rehash(hash_salvo)


@lru_cache
def hash_ficticio() -> str:
    """Hash usado para gastar o mesmo tempo quando o usuário não existe."""
    return _hasher.hash(secrets.token_urlsafe(16))


def segundos_validade_token() -> int:
    return int(timedelta(days=obter_config().jwt_expira_dias).total_seconds())


def _criar_token(
    usuario_id: int, versao_token: int, validade: timedelta, escopo: str | None
) -> str:
    emitido_em = agora()
    claims = {
        "sub": str(usuario_id),
        "tv": versao_token,
        "iat": emitido_em,
        "exp": emitido_em + validade,
    }
    if escopo is not None:
        claims["escopo"] = escopo
    chave = obter_config().secret_key.get_secret_value()
    return jwt.encode(claims, chave, algorithm=ALGORITMO_JWT)


def _decodificar_token(token: str, escopo: str | None) -> tuple[int, int]:
    chave = obter_config().secret_key.get_secret_value()
    try:
        claims = jwt.decode(
            token,
            chave,
            algorithms=[ALGORITMO_JWT],
            options={"require": ["exp", "sub", "tv"]},
        )
        # Um token só vale para o fim com que foi emitido.
        if claims.get("escopo") != escopo:
            raise TokenInvalido
        return int(claims["sub"]), int(claims["tv"])
    except (jwt.InvalidTokenError, ValueError, TypeError) as erro:
        raise TokenInvalido from erro


def criar_token(usuario_id: int, versao_token: int) -> str:
    validade = timedelta(seconds=segundos_validade_token())
    return _criar_token(usuario_id, versao_token, validade, escopo=None)


def decodificar_token(token: str) -> tuple[int, int]:
    """Devolve (usuario_id, versao_token) ou levanta TokenInvalido."""
    return _decodificar_token(token, escopo=None)


def criar_token_primeiro_acesso(usuario_id: int, versao_token: int) -> str:
    """Token curto que só serve para concluir o primeiro acesso."""
    return _criar_token(
        usuario_id,
        versao_token,
        VALIDADE_TOKEN_PRIMEIRO_ACESSO,
        escopo=ESCOPO_PRIMEIRO_ACESSO,
    )


def decodificar_token_primeiro_acesso(token: str) -> tuple[int, int]:
    """Devolve (usuario_id, versao_token) ou levanta TokenInvalido."""
    return _decodificar_token(token, escopo=ESCOPO_PRIMEIRO_ACESSO)


def gerar_codigo() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_codigo(usuario_id: int, codigo: str) -> str:
    # HMAC com a chave do servidor: um SHA-256 puro de 6 dígitos seria
    # revertido por força bruta caso o banco vazasse.
    chave = obter_config().secret_key.get_secret_value().encode()
    return hmac.new(
        chave, f"{usuario_id}:{codigo}".encode(), hashlib.sha256
    ).hexdigest()
