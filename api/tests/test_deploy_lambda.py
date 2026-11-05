import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core import parametros
from src.core.origem import ExigirCloudFront
from src.scripts import limpar_pacotes_deploy

# --- Parameter Store ---


class SsmFalso:
    def __init__(self, paginas):
        self.paginas = paginas
        self.chamadas = []

    def get_paginator(self, operacao):
        assert operacao == "get_parameters_by_path"
        return self

    def paginate(self, **argumentos):
        self.chamadas.append(argumentos)
        return iter(self.paginas)


def _parametro(nome, valor):
    return {"Name": nome, "Value": valor}


@pytest.fixture
def ambiente(monkeypatch):
    """Variáveis de ambiente isoladas: o que o teste grava não vaza para os outros."""
    variaveis = {}
    monkeypatch.setattr(parametros.os, "environ", variaveis)
    return variaveis


def test_parametros_viram_variaveis_de_ambiente(ambiente):
    ambiente["SSM_PREFIXO"] = "/homolog/"
    cliente = SsmFalso(
        [
            {"Parameters": [_parametro("/homolog/database_url", "postgresql://x")]},
            {"Parameters": [_parametro("/homolog/push_backend", "expo")]},
        ]
    )
    assert parametros.carregar_parametros(cliente) == 2
    assert cliente.chamadas == [
        {"Path": "/homolog", "WithDecryption": True, "Recursive": False}
    ]
    assert ambiente["DATABASE_URL"] == "postgresql://x"
    assert ambiente["PUSH_BACKEND"] == "expo"


def test_parametros_nao_sobrescrevem_variaveis(ambiente):
    ambiente.update(SSM_PREFIXO="/prod/", AMBIENTE="prod")
    cliente = SsmFalso([{"Parameters": [_parametro("/prod/ambiente", "outro")]}])
    assert parametros.carregar_parametros(cliente) == 0
    assert ambiente["AMBIENTE"] == "prod"


def test_sem_prefixo_nada_acontece(ambiente):
    cliente = SsmFalso([])
    assert parametros.carregar_parametros(cliente) == 0
    assert cliente.chamadas == []


# --- origem pelo CloudFront ---


@pytest.fixture
def cliente_protegido():
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(ExigirCloudFront, segredo="segredo-do-ambiente")
    return TestClient(app)


@pytest.mark.parametrize("cabecalhos", [{}, {"X-Origem-Cloudfront": "errado"}])
def test_sem_o_cabecalho_do_cloudfront_responde_403(cliente_protegido, cabecalhos):
    resposta = cliente_protegido.get("/ping", headers=cabecalhos)
    assert resposta.status_code == 403
    assert resposta.json() == {
        "sucesso": False,
        "mensagem": "Acesso não permitido",
        "dados": None,
    }


def test_com_o_cabecalho_do_cloudfront_passa(cliente_protegido):
    resposta = cliente_protegido.get(
        "/ping", headers={"X-Origem-Cloudfront": "segredo-do-ambiente"}
    )
    assert resposta.status_code == 200


# --- pontos de entrada da Lambda ---


def _evento_da_function_url(caminho):
    dominio = "abc.lambda-url.us-east-1.on.aws"
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": caminho,
        "rawQueryString": "",
        "headers": {"host": dominio, "x-forwarded-proto": "https"},
        "requestContext": {
            "accountId": "anonymous",
            "apiId": "abc",
            "domainName": dominio,
            "domainPrefix": "abc",
            "http": {
                "method": "GET",
                "path": caminho,
                "protocol": "HTTP/1.1",
                "sourceIp": "203.0.113.1",
                "userAgent": "teste",
            },
            "requestId": "id",
            "routeKey": "$default",
            "stage": "$default",
            "time": "27/Oct/2026:12:00:00 +0000",
            "timeEpoch": 1_793_102_400_000,
        },
        "isBase64Encoded": False,
    }


def test_handler_responde_ao_evento_da_function_url():
    import lambda_handler

    resposta = lambda_handler.handler(
        _evento_da_function_url("/api/health"), SimpleNamespace()
    )
    assert resposta["statusCode"] == 200
    assert json.loads(resposta["body"])["status"] == "ok"


def test_tarefa_processa_a_fila(monkeypatch, capsys):
    import lambda_tarefa

    resultado = {"enviadas": 2, "recibos_conferidos": 1}
    monkeypatch.setattr(lambda_tarefa, "executar_tarefa_agendada", lambda: resultado)
    assert lambda_tarefa.handler({}, SimpleNamespace()) == resultado
    assert json.loads(capsys.readouterr().out) == resultado


# --- limpeza dos pacotes no S3 ---


def _objeto(chave, horas_atras):
    return {
        "Key": chave,
        "LastModified": datetime.now(UTC) - timedelta(hours=horas_atras),
    }


def test_mantem_os_cinco_mais_recentes_de_cada_tipo():
    pacotes = [_objeto(f"prod/pacote{n}", n) for n in range(7)]
    templates = [_objeto(f"prod/t{n}.template", n) for n in range(6)]
    apagar = limpar_pacotes_deploy.objetos_a_apagar(pacotes + templates, manter=5)
    assert sorted(apagar) == ["prod/pacote5", "prod/pacote6", "prod/t5.template"]


class S3Falso:
    def __init__(self, objetos):
        self.objetos = objetos
        self.apagados = []

    def get_paginator(self, operacao):
        assert operacao == "list_objects_v2"
        return self

    def paginate(self, Bucket, Prefix):
        return [{"Contents": [o for o in self.objetos if o["Key"].startswith(Prefix)]}]

    def delete_objects(self, Bucket, Delete):
        self.apagados.extend(item["Key"] for item in Delete["Objects"])


def test_limpa_so_o_prefixo_do_ambiente():
    objetos = [_objeto(f"homolog/p{n}", n) for n in range(6)]
    objetos += [_objeto(f"prod/p{n}", n) for n in range(6)]
    cliente = S3Falso(objetos)
    assert limpar_pacotes_deploy.limpar(cliente, "bucket", "prod") == 1
    assert cliente.apagados == ["prod/p5"]
