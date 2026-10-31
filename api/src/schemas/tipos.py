"""Tipos anotados reutilizáveis para higienizar dados vindos do front."""

import re
import unicodedata
from itertools import cycle
from typing import Annotated

from pydantic import (
    AfterValidator,
    BeforeValidator,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    TypeAdapter,
    ValidationError,
)

TAMANHO_MAXIMO_EMAIL = 80
MINIMO_ESPECIAIS_SENHA = 2
# Maior valor de uma coluna integer do PostgreSQL.
ID_MAXIMO = 2_147_483_647
# Tamanho máximo de uma chave Pix do tipo e-mail.
TAMANHO_MAXIMO_CHAVE_PIX = 77
MAXIMO_IDS_POR_CHAMADA = 100


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

# Termo de busca das listagens. Recusa caracteres de controle porque o
# PostgreSQL não aceita NUL em texto.
Busca = Annotated[
    str,
    AfterValidator(_normalizar_nome),
    StringConstraints(max_length=100),
]


def _normalizar_cnpj(valor: object) -> object:
    return _apenas_digitos(valor).upper() if isinstance(valor, str) else valor


def _digito_verificador_cnpj(base: str) -> str:
    # No CNPJ alfanumérico cada caractere vale o código ASCII menos 48, o que
    # mantém os dígitos com o próprio valor.
    soma = sum(
        (ord(caractere) - 48) * peso
        for caractere, peso in zip(reversed(base), cycle(range(2, 10)), strict=False)
    )
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def _validar_cnpj(valor: str) -> str:
    if len(set(valor)) == 1:
        raise ValueError("CNPJ inválido")
    primeiro = _digito_verificador_cnpj(valor[:12])
    segundo = _digito_verificador_cnpj(valor[:12] + primeiro)
    if valor[12:] != primeiro + segundo:
        raise ValueError("CNPJ inválido")
    return valor


_PADRAO_CNPJ = r"^[0-9A-Z]{12}[0-9]{2}$"

# Guardado sem máscara. Aceita o formato numérico e o alfanumérico (letras nas
# 12 primeiras posições), em vigor desde julho de 2026.
Cnpj = Annotated[
    str,
    BeforeValidator(_normalizar_cnpj),
    StringConstraints(pattern=_PADRAO_CNPJ),
    AfterValidator(_validar_cnpj),
]

_PADRAO_CHAVE_ALEATORIA = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_PADRAO_TELEFONE_PIX = re.compile(r"^\+55[1-9][0-9]{9,10}$")


def _normalizar_chave_pix(valor: str) -> str:
    """Identifica o tipo da chave e a devolve no formato em que o Pix a guarda."""
    valor = valor.strip()
    if "@" in valor:
        try:
            email = TypeAdapter(Email).validate_python(valor)
        except ValidationError:
            raise ValueError("chave Pix inválida") from None
        if len(email) > TAMANHO_MAXIMO_CHAVE_PIX:
            raise ValueError("chave Pix inválida")
        return email
    if _PADRAO_CHAVE_ALEATORIA.match(valor.lower()):
        return valor.lower()
    if valor.startswith("+"):
        telefone = "+" + _apenas_digitos(valor[1:])
        if _PADRAO_TELEFONE_PIX.match(telefone):
            return telefone
        raise ValueError("chave Pix inválida")

    documento = _normalizar_cnpj(valor)
    try:
        if re.fullmatch(r"[0-9]{11}", documento):
            return _validar_cpf(documento)
        if re.fullmatch(_PADRAO_CNPJ, documento):
            return _validar_cnpj(documento)
    except ValueError:
        pass
    raise ValueError("chave Pix inválida")


# CPF, CNPJ, e-mail, telefone (com +55) ou chave aleatória.
ChavePix = Annotated[
    str,
    StringConstraints(max_length=100),
    AfterValidator(_normalizar_chave_pix),
]

TituloGrupo = Annotated[
    str,
    AfterValidator(_normalizar_nome),
    StringConstraints(min_length=1, max_length=50),
]
DescricaoGrupo = Annotated[
    str,
    AfterValidator(_normalizar_nome),
    StringConstraints(min_length=1, max_length=100),
]

IdBanco = Annotated[int, Field(ge=1, le=ID_MAXIMO)]


def _sem_repeticao(ids: list[int]) -> list[int]:
    if len(set(ids)) != len(ids):
        raise ValueError("a lista não pode ter ids repetidos")
    return ids


IdsDeAlunos = Annotated[
    list[IdBanco],
    Field(max_length=MAXIMO_IDS_POR_CHAMADA),
    AfterValidator(_sem_repeticao),
]
