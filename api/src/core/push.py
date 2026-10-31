"""Envio de notificações push pelo Expo Push Service.

O app registra o ExpoPushToken; o Expo entrega pelo FCM (Android) e pelo APNs (iOS).
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from src.core.config import obter_config

logger = logging.getLogger(__name__)

URL_ENVIO = "https://exp.host/--/api/v2/push/send"
URL_RECIBOS = "https://exp.host/--/api/v2/push/getReceipts"
TIMEOUT_SEGUNDOS = 10
# Limites de cada chamada da API do Expo.
MENSAGENS_POR_ENVIO = 100
IDS_POR_CONSULTA_DE_RECIBOS = 1000
# Erro do Expo para token que não vale mais (app desinstalado, por exemplo).
DISPOSITIVO_NAO_REGISTRADO = "DeviceNotRegistered"


class FalhaPush(Exception):
    """O Expo não respondeu ou recusou a chamada inteira. Vale tentar de novo depois."""


@dataclass(frozen=True)
class MensagemPush:
    token: str
    titulo: str
    corpo: str
    dados: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Ticket:
    """Resultado de uma mensagem. `id` serve para consultar o recibo depois."""

    ok: bool
    id: str | None = None
    erro: str | None = None


@dataclass(frozen=True)
class Recibo:
    ok: bool
    erro: str | None = None


class EnviadorPush(Protocol):
    def enviar(self, mensagens: list[MensagemPush]) -> list[Ticket]:
        """Um ticket por mensagem, na mesma ordem. Levanta FalhaPush."""
        ...

    def consultar_recibos(self, ids: list[str]) -> dict[str, Recibo]:
        """Só traz os recibos já disponíveis. Levanta FalhaPush."""
        ...


class EnviadorPushConsole:
    """Apenas registra as mensagens no log. Para desenvolvimento e testes."""

    def enviar(self, mensagens: list[MensagemPush]) -> list[Ticket]:
        for mensagem in mensagens:
            logger.warning(
                "Push para %s | %s\n%s\n%s",
                mensagem.token,
                mensagem.titulo,
                mensagem.corpo,
                mensagem.dados,
            )
        return [Ticket(ok=True) for _ in mensagens]

    def consultar_recibos(self, ids: list[str]) -> dict[str, Recibo]:
        return {}


def _erro(item: dict[str, Any]) -> str:
    detalhes = item.get("details") or {}
    erro = detalhes.get("error") or item.get("message") or "erro desconhecido"
    return str(erro)[:100]


class EnviadorPushExpo:
    def _chamar(self, url: str, corpo: object) -> Any:
        cabecalhos = {"Accept": "application/json", "Content-Type": "application/json"}
        token = obter_config().expo_access_token
        if token is not None:
            cabecalhos["Authorization"] = f"Bearer {token.get_secret_value()}"
        requisicao = urllib.request.Request(
            url, data=json.dumps(corpo).encode(), headers=cabecalhos, method="POST"
        )
        try:
            with urllib.request.urlopen(
                requisicao, timeout=TIMEOUT_SEGUNDOS
            ) as resposta:
                return json.loads(resposta.read())["data"]
        except urllib.error.HTTPError as erro:
            raise FalhaPush(f"Expo respondeu {erro.code}") from erro
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as erro:
            raise FalhaPush(f"falha na chamada ao Expo: {erro}") from erro

    def enviar(self, mensagens: list[MensagemPush]) -> list[Ticket]:
        tickets: list[Ticket] = []
        for inicio in range(0, len(mensagens), MENSAGENS_POR_ENVIO):
            lote = mensagens[inicio : inicio + MENSAGENS_POR_ENVIO]
            itens = self._chamar(
                URL_ENVIO,
                [
                    {
                        "to": mensagem.token,
                        "title": mensagem.titulo,
                        "body": mensagem.corpo,
                        "data": mensagem.dados,
                        "sound": "default",
                    }
                    for mensagem in lote
                ],
            )
            if len(itens) != len(lote):
                raise FalhaPush("o Expo devolveu um número inesperado de tickets")
            tickets.extend(
                Ticket(ok=True, id=item.get("id"))
                if item.get("status") == "ok"
                else Ticket(ok=False, erro=_erro(item))
                for item in itens
            )
        return tickets

    def consultar_recibos(self, ids: list[str]) -> dict[str, Recibo]:
        recibos: dict[str, Recibo] = {}
        for inicio in range(0, len(ids), IDS_POR_CONSULTA_DE_RECIBOS):
            lote = ids[inicio : inicio + IDS_POR_CONSULTA_DE_RECIBOS]
            itens = self._chamar(URL_RECIBOS, {"ids": lote})
            for ticket_id, item in itens.items():
                recibos[ticket_id] = (
                    Recibo(ok=True)
                    if item.get("status") == "ok"
                    else Recibo(ok=False, erro=_erro(item))
                )
        return recibos


def obter_enviador_push() -> EnviadorPush:
    if obter_config().push_backend == "expo":
        return EnviadorPushExpo()
    return EnviadorPushConsole()
