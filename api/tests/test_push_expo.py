import http.client
import io
import json
import urllib.error
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from src.core import push
from src.core.push import EnviadorPushExpo, FalhaPush, MensagemPush, Recibo, Ticket


class UrlopenFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.requisicoes = []

    def __call__(self, requisicao, timeout):
        self.requisicoes.append(requisicao)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return io.BytesIO(json.dumps(resposta).encode())

    def corpo(self, indice=0):
        return json.loads(self.requisicoes[indice].data)


@pytest.fixture
def urlopen(monkeypatch):
    def _instalar(*respostas, access_token=None):
        falso = UrlopenFalso(respostas)
        monkeypatch.setattr(push.urllib.request, "urlopen", falso)
        monkeypatch.setattr(
            push,
            "obter_config",
            lambda: SimpleNamespace(
                expo_access_token=SecretStr(access_token) if access_token else None
            ),
        )
        return falso

    return _instalar


def _mensagens(quantidade):
    return [
        MensagemPush(
            token=f"ExponentPushToken[{indice}]",
            titulo="Novo recado",
            corpo="Aula cancelada",
            dados={"recado_id": 1},
        )
        for indice in range(quantidade)
    ]


def test_envia_no_formato_do_expo(urlopen):
    falso = urlopen({"data": [{"status": "ok", "id": "t-1"}]})
    tickets = EnviadorPushExpo().enviar(_mensagens(1))

    assert tickets == [Ticket(ok=True, id="t-1")]
    requisicao = falso.requisicoes[0]
    assert requisicao.full_url == push.URL_ENVIO
    assert requisicao.get_method() == "POST"
    assert requisicao.get_header("Content-type") == "application/json"
    assert requisicao.get_header("Authorization") is None
    assert falso.corpo() == [
        {
            "to": "ExponentPushToken[0]",
            "title": "Novo recado",
            "body": "Aula cancelada",
            "data": {"recado_id": 1},
            "sound": "default",
        }
    ]


def test_usa_o_access_token_quando_configurado(urlopen):
    falso = urlopen({"data": [{"status": "ok", "id": "t-1"}]}, access_token="segredo")
    EnviadorPushExpo().enviar(_mensagens(1))
    assert falso.requisicoes[0].get_header("Authorization") == "Bearer segredo"


def test_divide_em_lotes_de_100(urlopen):
    falso = urlopen(
        {"data": [{"status": "ok", "id": f"a{i}"} for i in range(100)]},
        {"data": [{"status": "ok", "id": f"b{i}"} for i in range(50)]},
    )
    tickets = EnviadorPushExpo().enviar(_mensagens(150))
    assert len(tickets) == 150
    assert [len(falso.corpo(indice)) for indice in range(2)] == [100, 50]


def test_ticket_com_erro(urlopen):
    urlopen(
        {
            "data": [
                {
                    "status": "error",
                    "message": "não registrado",
                    "details": {"error": "DeviceNotRegistered"},
                },
                {"status": "error", "message": "outro problema"},
            ]
        }
    )
    tickets = EnviadorPushExpo().enviar(_mensagens(2))
    assert tickets == [
        Ticket(ok=False, erro="DeviceNotRegistered"),
        Ticket(ok=False, erro="outro problema"),
    ]


@pytest.mark.parametrize(
    "resposta",
    [
        urllib.error.HTTPError(push.URL_ENVIO, 429, "Too Many Requests", {}, None),
        urllib.error.HTTPError(push.URL_ENVIO, 500, "Server Error", {}, None),
        urllib.error.URLError("sem rede"),
        TimeoutError(),
        {"inesperado": True},
        {"data": []},
    ],
)
def test_falhas_viram_falha_push(urlopen, resposta):
    urlopen(resposta)
    with pytest.raises(FalhaPush):
        EnviadorPushExpo().enviar(_mensagens(1))


def test_consulta_os_recibos(urlopen):
    falso = urlopen(
        {
            "data": {
                "t-1": {"status": "ok"},
                "t-2": {"status": "error", "details": {"error": "DeviceNotRegistered"}},
            }
        }
    )
    recibos = EnviadorPushExpo().consultar_recibos(["t-1", "t-2", "t-3"])
    assert recibos == {
        "t-1": Recibo(ok=True),
        "t-2": Recibo(ok=False, erro="DeviceNotRegistered"),
    }
    assert falso.requisicoes[0].full_url == push.URL_RECIBOS
    assert falso.corpo() == {"ids": ["t-1", "t-2", "t-3"]}


@pytest.mark.parametrize(
    "erro",
    [
        ConnectionResetError("conexão caiu"),
        http.client.IncompleteRead(b""),
        http.client.RemoteDisconnected("fechou sem responder"),
    ],
)
def test_erro_ao_ler_a_resposta_vira_falha_push(monkeypatch, urlopen, erro):
    urlopen()

    class RespostaQueQuebra(io.BytesIO):
        def read(self, *_):
            raise erro

    monkeypatch.setattr(
        push.urllib.request, "urlopen", lambda *_, **__: RespostaQueQuebra()
    )
    with pytest.raises(FalhaPush):
        EnviadorPushExpo().enviar(_mensagens(1))


def test_timeout_de_cada_enviador(monkeypatch):
    monkeypatch.setattr(
        push, "obter_config", lambda: SimpleNamespace(push_backend="expo")
    )
    assert push.obter_enviador_push().timeout_segundos == push.TIMEOUT_SEGUNDOS
    assert (
        push.obter_enviador_push_na_requisicao().timeout_segundos
        == push.TIMEOUT_NA_REQUISICAO_SEGUNDOS
    )
