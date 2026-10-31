"""Configuração vinda do Parameter Store, na AWS Lambda.

O template define `SSM_PREFIXO` (por exemplo, `/prod/`). Na partida da
instância, cada parâmetro desse prefixo vira uma variável de ambiente com o
nome final em maiúsculas (`/prod/database_url` → `DATABASE_URL`), que o
`Config` lê como se viesse do `.env`. Sem `SSM_PREFIXO`, localmente e nos
testes, nada acontece.
"""

import os
from typing import Any

VARIAVEL_DO_PREFIXO = "SSM_PREFIXO"


def _cliente_ssm() -> Any:
    # O boto3 vem no runtime Python da Lambda; fora dela, só no grupo dev.
    import boto3

    return boto3.client("ssm")


def carregar_parametros(cliente: Any = None) -> int:
    """Grava os parâmetros do prefixo em `os.environ`, sem sobrescrever o que
    já está definido. Devolve quantos foram gravados."""
    prefixo = os.getenv(VARIAVEL_DO_PREFIXO)
    if not prefixo:
        return 0
    if cliente is None:
        cliente = _cliente_ssm()

    gravados = 0
    paginas = cliente.get_paginator("get_parameters_by_path").paginate(
        Path=prefixo.rstrip("/"), WithDecryption=True, Recursive=False
    )
    for pagina in paginas:
        for parametro in pagina["Parameters"]:
            nome = parametro["Name"].rsplit("/", 1)[-1].upper()
            if nome not in os.environ:
                os.environ[nome] = parametro["Value"]
                gravados += 1
    return gravados
