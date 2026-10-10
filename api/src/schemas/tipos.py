"""Tipos anotados reutilizáveis para higienizar dados vindos do front."""

import unicodedata
from typing import Annotated

from pydantic import (
    AfterValidator,
    BeforeValidator,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
)

TAMANHO_MAXIMO_EMAIL = 80
MINIMO_ESPECIAIS_SENHA = 2


def _remover_espacos_das_pontas(valor: object) -> object:
    return valor.strip() if isinstance(valor, str) else valor


def _normalizar_email(valor: str) -> str:
    valor = valor.lower()
    if len(valor) > TAMANHO_MAXIMO_EMAIL:
        raise ValueError(
            f"o e-mail deve ter no máximo {TAMANHO_MAXIMO_EMAIL} caracteres"
        )
    return valor


def _normalizar_nome(valor: str) -> str:
    valor = " ".join(unicodedata.normalize("NFC", valor).split())
    if any(unicodedata.category(caractere).startswith("C") for caractere in valor):
        raise ValueError("o nome contém caracteres inválidos")
    return valor


Email = Annotated[
    EmailStr,
    BeforeValidator(_remover_espacos_das_pontas),
    AfterValidator(_normalizar_email),
]

NomeCompleto = Annotated[
    str,
    AfterValidator(_normalizar_nome),
    StringConstraints(min_length=3, max_length=100),
]


def _validar_composicao_da_senha(senha: SecretStr) -> SecretStr:
    valor = senha.get_secret_value()
    especiais = sum(
        1 for caractere in valor if not caractere.isalnum() and not caractere.isspace()
    )
    if (
        not any(caractere.islower() for caractere in valor)
        or not any(caractere.isupper() for caractere in valor)
        or especiais < MINIMO_ESPECIAIS_SENHA
    ):
        raise ValueError(
            "a senha deve ter ao menos 1 letra minúscula, 1 maiúscula e "
            f"{MINIMO_ESPECIAIS_SENHA} caracteres especiais"
        )
    return senha


def _apenas_digitos(valor: object) -> object:
    """Aceita o valor com máscara ("123.456.789-09", "(11) 91234-5678")."""
    if not isinstance(valor, str):
        return valor
    return "".join(caractere for caractere in valor if caractere not in " .-()/")


def _digito_verificador_cpf(digitos: str) -> str:
    soma = sum(
        int(digito) * peso
        for digito, peso in zip(digitos, range(len(digitos) + 1, 1, -1), strict=True)
    )
    return str((soma * 10) % 11 % 10)


def _validar_cpf(valor: str) -> str:
    if len(set(valor)) == 1:
        raise ValueError("CPF inválido")
    primeiro = _digito_verificador_cpf(valor[:9])
    segundo = _digito_verificador_cpf(valor[:9] + primeiro)
    if valor[9:] != primeiro + segundo:
        raise ValueError("CPF inválido")
    return valor


# Senhas não passam por strip nem normalização: o que o usuário digitou é o que vale.
# O teto de caracteres limita o custo de CPU do Argon2.
NovaSenha = Annotated[
    SecretStr,
    Field(min_length=6, max_length=100),
    AfterValidator(_validar_composicao_da_senha),
]
SenhaLogin = Annotated[SecretStr, Field(min_length=1, max_length=128)]

Codigo = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9]{6}$")]

# Guardados só com dígitos. Telefone: DDD + número (fixo ou celular).
Cpf = Annotated[
    str,
    BeforeValidator(_apenas_digitos),
    StringConstraints(pattern=r"^[0-9]{11}$"),
    AfterValidator(_validar_cpf),
]
Telefone = Annotated[
    str,
    BeforeValidator(_apenas_digitos),
    StringConstraints(pattern=r"^[1-9][0-9]{9,10}$"),
]
