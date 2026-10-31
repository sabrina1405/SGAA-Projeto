"""Deixa no S3 só os pacotes mais recentes de um ambiente.

O SAM sobe, a cada deploy com mudança, o pacote do código e o template, com
nomes por hash, no prefixo do ambiente. Ficam os 5 mais recentes de cada
tipo, para voltar atrás sem reconstruir.

Uso (chamado pelo deploy_lambda.sh):
    poetry run python -m src.scripts.limpar_pacotes_deploy <bucket> <homolog|prod>
"""

import sys
from typing import Any

MANTIDOS = 5
# Limite da API do S3 por chamada de exclusão.
EXCLUSOES_POR_CHAMADA = 1000


def objetos_a_apagar(objetos: list[dict[str, Any]], manter: int) -> list[str]:
    """Chaves além das `manter` mais recentes, separando templates e pacotes."""
    templates = [objeto for objeto in objetos if objeto["Key"].endswith(".template")]
    pacotes = [objeto for objeto in objetos if not objeto["Key"].endswith(".template")]
    apagar = []
    for grupo in (templates, pacotes):
        grupo.sort(key=lambda objeto: objeto["LastModified"], reverse=True)
        apagar.extend(objeto["Key"] for objeto in grupo[manter:])
    return apagar


def limpar(cliente: Any, bucket: str, prefixo: str, manter: int = MANTIDOS) -> int:
    """Apaga os pacotes antigos do prefixo. Devolve quantos foram apagados."""
    objetos = [
        objeto
        for pagina in cliente.get_paginator("list_objects_v2").paginate(
            Bucket=bucket, Prefix=f"{prefixo}/"
        )
        for objeto in pagina.get("Contents", [])
    ]
    apagar = objetos_a_apagar(objetos, manter)
    for inicio in range(0, len(apagar), EXCLUSOES_POR_CHAMADA):
        lote = apagar[inicio : inicio + EXCLUSOES_POR_CHAMADA]
        cliente.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": chave} for chave in lote], "Quiet": True},
        )
    return len(apagar)


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ("homolog", "prod"):
        sys.exit(__doc__)
    import boto3

    bucket, prefixo = sys.argv[1], sys.argv[2]
    apagados = limpar(boto3.client("s3"), bucket, prefixo)
    print(f"Pacotes antigos apagados em s3://{bucket}/{prefixo}/: {apagados}")


if __name__ == "__main__":
    main()
