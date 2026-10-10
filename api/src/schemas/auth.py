from typing import Self

from pydantic import BaseModel, model_validator

from src.schemas.base import SchemaEntrada
from src.schemas.tipos import Codigo, Email, NovaSenha, SenhaLogin
from src.schemas.usuario import UsuarioResposta


class LoginEntrada(SchemaEntrada):
    email: Email
    senha: SenhaLogin


class EsqueciSenhaEntrada(SchemaEntrada):
    email: Email


class RedefinirSenhaEntrada(SchemaEntrada):
    email: Email
    codigo: Codigo
    nova_senha: NovaSenha

    @model_validator(mode="after")
    def _senha_diferente_do_email(self) -> Self:
        if self.nova_senha.get_secret_value().lower() == self.email:
            raise ValueError("a senha não pode ser igual ao e-mail")
        return self


class PrimeiroAcessoCodigoEntrada(SchemaEntrada):
    email: Email


class PrimeiroAcessoValidarEntrada(SchemaEntrada):
    email: Email
    codigo: Codigo


class TokenResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioResposta


class TokenPrimeiroAcessoResposta(BaseModel):
    """Token que só serve para enviar o formulário de primeiro acesso."""

    token_primeiro_acesso: str
    expires_in: int
    usuario: UsuarioResposta


class MensagemResposta(BaseModel):
    mensagem: str
