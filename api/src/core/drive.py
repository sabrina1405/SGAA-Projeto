"""Arquivos no Google Drive, na conta do projeto, com OAuth e a `urllib`.

A API não recebe o arquivo: ela abre uma sessão de upload, o app envia direto ao
Google e a API confere o resultado. Passando pela Lambda, 5 MB em base64
estourariam os 6 MB da Function URL.

Cada ambiente usa uma pasta própria, e só os arquivos dela são reconhecidos: os
ids de `arquivo` se repetem entre homologação e produção.
"""

import http.client
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message
from typing import Protocol

from src.core.config import obter_config

logger = logging.getLogger(__name__)

URL_TOKEN = "https://oauth2.googleapis.com/token"
URL_ARQUIVOS = "https://www.googleapis.com/drive/v3/files"
URL_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
TIMEOUT_SEGUNDOS = 10
# Dentro de uma requisição, a espera soma no tempo de resposta. Confirmar um
# arquivo faz até 3 chamadas, o que fica abaixo do timeout de 15 s da Lambda.
TIMEOUT_NA_REQUISICAO_SEGUNDOS = 3
# Renova o token um pouco antes de expirar.
FOLGA_DO_TOKEN_SEGUNDOS = 60
CAMPOS_DO_ARQUIVO = "id,size,mimeType,appProperties,parents,webViewLink"


class FalhaDrive(Exception):
    """O Drive não respondeu ou recusou a chamada. Vale tentar de novo depois."""


class _NaoEncontradoNoDrive(FalhaDrive):
    pass


@dataclass(frozen=True)
class ArquivoNoDrive:
    id: str
    tamanho: int
    tipo_mime: str
    arquivo_id: str | None
    url: str | None


class ArmazenamentoDrive(Protocol):
    def abrir_sessao(
        self,
        *,
        arquivo_id: int,
        nome: str,
        tipo_mime: str,
        tamanho: int,
        origem: str | None = None,
    ) -> str:
        """Devolve a URL para onde o app envia o arquivo. Levanta FalhaDrive."""
        ...

    def obter_arquivo(self, drive_file_id: str) -> ArquivoNoDrive | None:
        """None se o arquivo não existe na pasta do ambiente. Levanta FalhaDrive."""
        ...

    def compartilhar_por_link(self, drive_file_id: str) -> None:
        """Quem tem o link consegue ler. Levanta FalhaDrive."""
        ...

    def apagar(self, drive_file_id: str) -> None:
        """Apagar o que já não existe não é erro. Levanta FalhaDrive."""
        ...

    def buscar_por_arquivo_id(self, arquivo_id: int) -> list[str]:
        """Ids no Drive do `arquivo` cuja confirmação não chegou. Levanta FalhaDrive."""
        ...


class DriveDesligado:
    """Sem credenciais: desenvolvimento local e ambientes sem o Drive configurado."""

    def abrir_sessao(self, **_: object) -> str:
        raise FalhaDrive("Drive desligado")

    def obter_arquivo(self, drive_file_id: str) -> ArquivoNoDrive | None:
        raise FalhaDrive("Drive desligado")

    def compartilhar_por_link(self, drive_file_id: str) -> None:
        raise FalhaDrive("Drive desligado")

    def apagar(self, drive_file_id: str) -> None:
        raise FalhaDrive("Drive desligado")

    def buscar_por_arquivo_id(self, arquivo_id: int) -> list[str]:
        raise FalhaDrive("Drive desligado")


# No módulo, porque cada requisição cria um cliente novo: (token, expira_em).
_token_em_cache: tuple[str, float] | None = None


class DriveGoogle:
    def __init__(self, timeout_segundos: int = TIMEOUT_SEGUNDOS) -> None:
        self.timeout_segundos = timeout_segundos

    def _abrir(self, requisicao: urllib.request.Request) -> tuple[bytes, Message]:
        try:
            with urllib.request.urlopen(
                requisicao, timeout=self.timeout_segundos
            ) as resposta:
                return resposta.read(), resposta.headers
        except urllib.error.HTTPError as erro:
            if erro.code == 404:
                raise _NaoEncontradoNoDrive("não encontrado no Drive") from erro
            if erro.code == 401:
                _esquecer_token()
            raise FalhaDrive(f"Drive respondeu {erro.code}") from erro
        # OSError cobre URLError, TimeoutError e queda da conexão durante a leitura.
        except (OSError, http.client.HTTPException) as erro:
            raise FalhaDrive(f"falha na chamada ao Drive: {erro}") from erro

    def _token(self) -> str:
        global _token_em_cache
        if _token_em_cache is not None and _token_em_cache[1] > time.monotonic():
            return _token_em_cache[0]
        config = obter_config()
        segredo = config.google_drive_client_secret
        refresh_token = config.google_drive_refresh_token
        if segredo is None or refresh_token is None:
            raise FalhaDrive("credenciais do Drive não configuradas")
        corpo = urllib.parse.urlencode(
            {
                "client_id": config.google_drive_client_id,
                "client_secret": segredo.get_secret_value(),
                "refresh_token": refresh_token.get_secret_value(),
                "grant_type": "refresh_token",
            }
        ).encode()
        conteudo, _ = self._abrir(
            urllib.request.Request(URL_TOKEN, data=corpo, method="POST")
        )
        try:
            dados = json.loads(conteudo)
            token, validade = dados["access_token"], int(dados["expires_in"])
        except (ValueError, KeyError, TypeError) as erro:
            raise FalhaDrive("resposta inesperada ao renovar o token") from erro
        _token_em_cache = (
            token,
            time.monotonic() + validade - FOLGA_DO_TOKEN_SEGUNDOS,
        )
        return token

    def _chamar(
        self,
        metodo: str,
        url: str,
        corpo: object | None = None,
        cabecalhos: dict[str, str] | None = None,
    ) -> tuple[bytes, Message]:
        token = self._token()
        return self._abrir(
            urllib.request.Request(
                url,
                data=None if corpo is None else json.dumps(corpo).encode(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    **(cabecalhos or {}),
                },
                method=metodo,
            )
        )

    def abrir_sessao(
        self,
        *,
        arquivo_id: int,
        nome: str,
        tipo_mime: str,
        tamanho: int,
        origem: str | None = None,
    ) -> str:
        cabecalhos = {
            "X-Upload-Content-Type": tipo_mime,
            "X-Upload-Content-Length": str(tamanho),
        }
        if origem:
            # Sem a origem aqui, o navegador não consegue enviar à URL da sessão.
            cabecalhos["Origin"] = origem
        _, resposta = self._chamar(
            "POST",
            URL_UPLOAD,
            {
                "name": nome,
                "mimeType": tipo_mime,
                "parents": [obter_config().google_drive_pasta_id],
                "appProperties": {"arquivo_id": str(arquivo_id)},
            },
            cabecalhos,
        )
        url = resposta.get("Location")
        if not url:
            raise FalhaDrive("o Drive não devolveu a URL da sessão")
        return url

    def obter_arquivo(self, drive_file_id: str) -> ArquivoNoDrive | None:
        consulta = urllib.parse.urlencode({"fields": CAMPOS_DO_ARQUIVO})
        id_na_url = urllib.parse.quote(drive_file_id, safe="")
        try:
            conteudo, _ = self._chamar("GET", f"{URL_ARQUIVOS}/{id_na_url}?{consulta}")
        except _NaoEncontradoNoDrive:
            return None
        try:
            dados = json.loads(conteudo)
            if obter_config().google_drive_pasta_id not in dados.get("parents", []):
                return None
            return ArquivoNoDrive(
                id=dados["id"],
                tamanho=int(dados["size"]),
                tipo_mime=dados["mimeType"],
                arquivo_id=(dados.get("appProperties") or {}).get("arquivo_id"),
                url=dados.get("webViewLink"),
            )
        except (ValueError, KeyError, TypeError) as erro:
            raise FalhaDrive("resposta inesperada ao consultar o arquivo") from erro

    def compartilhar_por_link(self, drive_file_id: str) -> None:
        id_na_url = urllib.parse.quote(drive_file_id, safe="")
        self._chamar(
            "POST",
            f"{URL_ARQUIVOS}/{id_na_url}/permissions",
            {"type": "anyone", "role": "reader"},
        )

    def apagar(self, drive_file_id: str) -> None:
        id_na_url = urllib.parse.quote(drive_file_id, safe="")
        try:
            self._chamar("DELETE", f"{URL_ARQUIVOS}/{id_na_url}")
        except _NaoEncontradoNoDrive:
            logger.info("Arquivo %s já não existia no Drive", drive_file_id)

    def buscar_por_arquivo_id(self, arquivo_id: int) -> list[str]:
        pasta = obter_config().google_drive_pasta_id
        filtro = (
            f"appProperties has {{ key='arquivo_id' and value='{arquivo_id}' }} "
            f"and '{pasta}' in parents and trashed = false"
        )
        consulta = urllib.parse.urlencode({"q": filtro, "fields": "files(id)"})
        conteudo, _ = self._chamar("GET", f"{URL_ARQUIVOS}?{consulta}")
        try:
            return [item["id"] for item in json.loads(conteudo)["files"]]
        except (ValueError, KeyError, TypeError) as erro:
            raise FalhaDrive("resposta inesperada ao buscar arquivos") from erro


def _esquecer_token() -> None:
    global _token_em_cache
    _token_em_cache = None


def obter_drive() -> ArmazenamentoDrive:
    """Para a tarefa agendada."""
    if obter_config().drive_backend == "google":
        return DriveGoogle()
    return DriveDesligado()


def obter_drive_na_requisicao() -> ArmazenamentoDrive:
    """Para as rotas, com menos tempo de espera."""
    if obter_config().drive_backend == "google":
        return DriveGoogle(timeout_segundos=TIMEOUT_NA_REQUISICAO_SEGUNDOS)
    return DriveDesligado()
