"""Confere no Drive real o que os testes automáticos não alcançam. Usa as variáveis
GOOGLE_DRIVE_* do ambiente e apaga o que criou. Ver docs/google_drive.md.

Uso: poetry run python -m src.scripts.validar_drive --origem http://localhost:8081
"""

import argparse
import json
import urllib.error
import urllib.request

from src.core.drive import DriveGoogle

TIPO = "text/plain"
CONTEUDO = b"arquivo de teste do SGAA"
# Faixa alta, para não coincidir com um arquivo de verdade do ambiente.
PRIMEIRO_ID = 2_000_000_000


def _enviar(url: str, conteudo: bytes) -> tuple[int, dict]:
    requisicao = urllib.request.Request(
        url, data=conteudo, headers={"Content-Type": TIPO}, method="PUT"
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            return resposta.status, json.loads(resposta.read())
    except urllib.error.HTTPError as erro:
        return erro.code, {}


def _sessao(drive: DriveGoogle, arquivo_id: int, origem: str | None = None) -> str:
    return drive.abrir_sessao(
        arquivo_id=arquivo_id,
        nome="teste-sgaa.txt",
        tipo_mime=TIPO,
        tamanho=len(CONTEUDO),
        origem=origem,
    )


def main() -> None:
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--origem", required=True, help="origem do front web")
    origem = argumentos.parse_args().origem
    drive = DriveGoogle()
    ids = [PRIMEIRO_ID + indice for indice in range(3)]
    try:
        print("1. Envio normal")
        status, dados = _enviar(_sessao(drive, ids[0]), CONTEUDO)
        print(f"   HTTP {status}, id no Drive: {dados.get('id')}")
        arquivo = drive.obter_arquivo(dados["id"])
        print(f"   Conferido: {arquivo}")
        drive.compartilhar_por_link(dados["id"])
        print(f"   Abra em uma aba anônima, sem login: {arquivo.url}")

        print("2. Envio maior que o declarado")
        status, dados = _enviar(_sessao(drive, ids[1]), CONTEUDO * 2)
        print(f"   HTTP {status}. Recusado? {'sim' if status >= 400 else 'NÃO'}")
        if dados.get("id"):
            maior = drive.obter_arquivo(dados["id"])
            print(f"   Tamanho real no Drive: {maior.tamanho if maior else '?'}")

        print("3. Envio pelo navegador (CORS)")
        url = _sessao(drive, ids[2], origem)
        print(
            f"   Em uma página de {origem}, rode no console do navegador:\n\n"
            f"   fetch({json.dumps(url)}, {{method: 'PUT', headers: "
            f"{{'Content-Type': '{TIPO}'}}, body: 'teste'}})"
            ".then(r => r.json()).then(console.log).catch(console.error)\n"
        )
        print(
            "   Deve mostrar o id do arquivo. Erro de CORS no console significa "
            "que o envio direto não funciona na web."
        )
        input("   Enter para apagar os arquivos de teste... ")
    finally:
        for arquivo_id in ids:
            for drive_file_id in drive.buscar_por_arquivo_id(arquivo_id):
                drive.apagar(drive_file_id)
        print("Arquivos de teste apagados.")


if __name__ == "__main__":
    main()
