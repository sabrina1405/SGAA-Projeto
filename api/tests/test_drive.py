import http.client
import io
import json
import urllib.error
from email.message import Message
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from src.core import drive as modulo
from src.core.drive import DriveDesligado, DriveGoogle, FalhaDrive


class RespostaFalsa(io.BytesIO):
    def __init__(self, corpo=b"", cabecalhos=None):
        super().__init__(corpo)
        self.headers = Message()
        for nome, valor in (cabecalhos or {}).items():
            self.headers[nome] = valor


class UrlopenFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.requisicoes = []
        self.timeouts = []

    def __call__(self, requisicao, timeout):
        self.requisicoes.append(requisicao)
        self.timeouts.append(timeout)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _token(valor="token-1", expira=3600):
    return RespostaFalsa(
        json.dumps({"access_token": valor, "expires_in": expira}).encode()
    )


def _json(dados):
    return RespostaFalsa(json.dumps(dados).encode())


def _erro_http(codigo):
    return urllib.error.HTTPError("https://x", codigo, "erro", Message(), None)


@pytest.fixture
def urlopen(monkeypatch):
    def _instalar(*respostas):
        falso = UrlopenFalso(respostas)
        monkeypatch.setattr(modulo.urllib.request, "urlopen", falso)
        return falso

    monkeypatch.setattr(modulo, "_token_em_cache", None)
    monkeypatch.setattr(
        modulo,
        "obter_config",
        lambda: SimpleNamespace(
            drive_backend="google",
            google_drive_client_id="cliente",
            google_drive_client_secret=SecretStr("segredo"),
            google_drive_refresh_token=SecretStr("refresh"),
            google_drive_pasta_id="pasta-homolog",
        ),
    )
    return _instalar


def _metadados(**campos):
    return {
        "id": "abc",
        "size": "1024",
        "mimeType": "application/pdf",
        "appProperties": {"arquivo_id": "7"},
        "parents": ["pasta-homolog"],
        "webViewLink": "https://drive/ver/abc",
        **campos,
    }


def test_abre_a_sessao_com_os_metadados(urlopen):
    falso = urlopen(
        _token(), RespostaFalsa(cabecalhos={"Location": "https://upload/sessao"})
    )
    url = DriveGoogle().abrir_sessao(
        arquivo_id=7,
        nome="aula.pdf",
        tipo_mime="application/pdf",
        tamanho=1024,
        origem="https://app.exemplo",
    )
    assert url == "https://upload/sessao"
    requisicao = falso.requisicoes[1]
    assert json.loads(requisicao.data) == {
        "name": "aula.pdf",
        "mimeType": "application/pdf",
        "parents": ["pasta-homolog"],
        "appProperties": {"arquivo_id": "7"},
    }
    assert requisicao.get_header("Authorization") == "Bearer token-1"
    assert requisicao.get_header("X-upload-content-length") == "1024"
    assert requisicao.get_header("Origin") == "https://app.exemplo"


def test_sessao_sem_origem_nao_envia_o_cabecalho(urlopen):
    falso = urlopen(_token(), RespostaFalsa(cabecalhos={"Location": "https://u"}))
    DriveGoogle().abrir_sessao(
        arquivo_id=7, nome="a", tipo_mime="application/pdf", tamanho=1
    )
    assert falso.requisicoes[1].get_header("Origin") is None


def test_sessao_sem_location_e_falha(urlopen):
    urlopen(_token(), RespostaFalsa())
    with pytest.raises(FalhaDrive):
        DriveGoogle().abrir_sessao(
            arquivo_id=7, nome="a", tipo_mime="application/pdf", tamanho=1
        )


def test_reaproveita_o_token_entre_clientes(urlopen):
    falso = urlopen(_token(), _json(_metadados()), _json(_metadados()))
    DriveGoogle().obter_arquivo("abc")
    DriveGoogle().obter_arquivo("abc")
    assert len(falso.requisicoes) == 3


def test_renova_o_token_vencido(urlopen):
    falso = urlopen(
        _token("velho", expira=1), _json(_metadados()), _token("novo"), _json({})
    )
    drive = DriveGoogle()
    drive.obter_arquivo("abc")
    drive.compartilhar_por_link("abc")
    assert falso.requisicoes[3].get_header("Authorization") == "Bearer novo"


def test_401_esquece_o_token(urlopen):
    falso = urlopen(_token("velho"), _erro_http(401), _token("novo"), _json({}))
    drive = DriveGoogle()
    with pytest.raises(FalhaDrive):
        drive.compartilhar_por_link("abc")
    drive.compartilhar_por_link("abc")
    assert falso.requisicoes[3].get_header("Authorization") == "Bearer novo"


def test_sem_credenciais_e_falha(urlopen, monkeypatch):
    urlopen()
    monkeypatch.setattr(
        modulo,
        "obter_config",
        lambda: SimpleNamespace(
            google_drive_client_secret=None, google_drive_refresh_token=None
        ),
    )
    with pytest.raises(FalhaDrive):
        DriveGoogle().compartilhar_por_link("abc")


def test_obter_arquivo(urlopen):
    urlopen(_token(), _json(_metadados()))
    arquivo = DriveGoogle().obter_arquivo("abc")
    assert arquivo.tamanho == 1024
    assert arquivo.arquivo_id == "7"
    assert arquivo.url == "https://drive/ver/abc"


def test_arquivo_de_outra_pasta_nao_existe_para_o_ambiente(urlopen):
    urlopen(_token(), _json(_metadados(parents=["pasta-prod"])))
    assert DriveGoogle().obter_arquivo("abc") is None


def test_arquivo_inexistente(urlopen):
    urlopen(_token(), _erro_http(404))
    assert DriveGoogle().obter_arquivo("abc") is None


def test_apagar_o_que_nao_existe_nao_e_erro(urlopen):
    urlopen(_token(), _erro_http(404))
    DriveGoogle().apagar("abc")


def test_compartilhar_cria_a_permissao_de_leitura(urlopen):
    falso = urlopen(_token(), _json({}))
    DriveGoogle().compartilhar_por_link("abc")
    requisicao = falso.requisicoes[1]
    assert requisicao.full_url.endswith("/files/abc/permissions")
    assert json.loads(requisicao.data) == {"type": "anyone", "role": "reader"}


def test_busca_so_na_pasta_do_ambiente(urlopen):
    falso = urlopen(_token(), _json({"files": [{"id": "abc"}]}))
    assert DriveGoogle().buscar_por_arquivo_id(7) == ["abc"]
    url = modulo.urllib.parse.unquote_plus(falso.requisicoes[1].full_url)
    assert "value='7'" in url
    assert "'pasta-homolog' in parents" in url


@pytest.mark.parametrize(
    "erro",
    [
        _erro_http(500),
        urllib.error.URLError("sem rede"),
        TimeoutError("demorou"),
        ConnectionResetError("conexão caiu"),
        http.client.IncompleteRead(b""),
        http.client.RemoteDisconnected("fechou"),
    ],
)
def test_erros_viram_falha_drive(urlopen, erro):
    urlopen(_token(), erro)
    with pytest.raises(FalhaDrive):
        DriveGoogle().compartilhar_por_link("abc")


def test_resposta_ilegivel_vira_falha_drive(urlopen):
    urlopen(_token(), RespostaFalsa(b"nao-e-json"))
    with pytest.raises(FalhaDrive):
        DriveGoogle().obter_arquivo("abc")


def test_timeout_de_cada_cliente(urlopen):
    urlopen()
    assert modulo.obter_drive().timeout_segundos == modulo.TIMEOUT_SEGUNDOS
    assert (
        modulo.obter_drive_na_requisicao().timeout_segundos
        == modulo.TIMEOUT_NA_REQUISICAO_SEGUNDOS
    )


def test_drive_desligado_sempre_falha():
    drive = DriveDesligado()
    with pytest.raises(FalhaDrive):
        drive.abrir_sessao(arquivo_id=1, nome="a", tipo_mime="b", tamanho=1)
    with pytest.raises(FalhaDrive):
        drive.buscar_por_arquivo_id(1)
