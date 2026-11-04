import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.errors import MENSAGEM_ERRO_INTERNO, registrar_tratadores
from src.main import app, rotas_da_documentacao

client = TestClient(app)


def _erro(mensagem):
    return {"sucesso": False, "mensagem": mensagem, "dados": None}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_todas_as_rotas_da_api_tem_versao():
    caminhos = set(app.openapi()["paths"])
    assert len(caminhos) > 1
    assert {caminho for caminho in caminhos if not caminho.startswith("/v1/")} == {"/"}


def test_rota_sem_a_versao_nao_existe():
    assert client.get("/auth/me").status_code == 404
    assert client.post("/auth/login", json={}).status_code == 404


def test_rota_inexistente_responde_no_envelope():
    resposta = client.get("/v1/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json() == _erro("Recurso não encontrado")


def test_metodo_nao_permitido_responde_no_envelope():
    resposta = client.delete("/v1/auth/login")
    assert resposta.status_code == 405
    assert resposta.json() == _erro("Método não permitido")


def test_erro_nao_tratado_responde_500_sem_expor_a_excecao():
    app_com_falha = FastAPI()
    registrar_tratadores(app_com_falha)

    @app_com_falha.get("/falha")
    def falha():
        raise RuntimeError("detalhe interno que não pode vazar")

    resposta = TestClient(app_com_falha, raise_server_exceptions=False).get("/falha")
    assert resposta.status_code == 500
    assert resposta.json() == _erro(MENSAGEM_ERRO_INTERNO)
    assert "detalhe interno" not in resposta.text


@pytest.mark.parametrize(
    ("ambiente", "status"),
    [("prod", 404), ("homolog", 200), ("dev", 200), (None, 200)],
)
@pytest.mark.parametrize(
    "caminho", ["/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"]
)
def test_documentacao_so_fica_fora_do_ar_em_prod(ambiente, status, caminho):
    aplicacao = FastAPI(**rotas_da_documentacao(ambiente))
    assert TestClient(aplicacao).get(caminho).status_code == status


def test_swagger_documenta_o_envelope():
    esquema = app.openapi()
    login = esquema["paths"]["/v1/auth/login"]["post"]["responses"]
    assert login["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Resposta_TokenResposta_"
    }
    assert login["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RespostaErro"
    }
