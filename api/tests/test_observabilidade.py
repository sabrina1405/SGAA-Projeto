import json
from types import SimpleNamespace

import logfire
from fastapi import FastAPI

from src.core import observabilidade
from src.core.observabilidade import _sem_valores, configurar_observabilidade
from src.main import app

CPF = "52998224725"
SENHA = "Senha-Que-Nao-Pode-Vazar#1"
CODIGO = "codigo-que-nao-pode-vazar"


def test_mapper_descarta_valores_input_e_mensagem_dos_erros():
    atributos = {
        "values": {"dados": {"cpf": CPF, "nova_senha": SENHA}},
        "errors": [
            {
                "type": "value_error",
                "loc": ("body", "cpf"),
                "msg": f"Value error, CPF inválido: {CPF}",
                "input": CPF,
                "ctx": {"error": f"CPF inválido: {CPF}"},
            }
        ],
    }
    resultado = _sem_valores(None, atributos)
    assert resultado == {"errors": [{"type": "value_error", "loc": ("body", "cpf")}]}
    assert CPF not in json.dumps(resultado)


def test_mapper_sem_erros():
    assert _sem_valores(None, {"values": {"email": "a@b.com"}, "errors": []}) == {
        "errors": []
    }


def test_sem_token_nao_liga_nada(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        observabilidade.logfire, "configure", lambda **_: chamadas.append("configure")
    )
    monkeypatch.setattr(
        observabilidade, "obter_config", lambda: SimpleNamespace(logfire_token=None)
    )
    app_rotas, app_externo = FastAPI(), FastAPI()
    assert configurar_observabilidade(app_rotas, app_externo, "dev") is False
    assert chamadas == []
    assert app_externo.user_middleware == []


def test_requisicao_instrumentada_nao_exporta_dados_sensiveis(client, capfire):
    with logfire.instrument_fastapi(app, request_attributes_mapper=_sem_valores):
        invalida = client.post(
            "/v1/auth/primeiro-acesso/validar-codigo",
            json={"email": "vazamento@exemplo.com", "codigo": CODIGO},
        )
        login = client.post(
            "/v1/auth/login", json={"email": "vazamento@exemplo.com", "senha": SENHA}
        )
    assert invalida.status_code == 422
    assert login.status_code == 401

    spans = capfire.exporter.exported_spans_as_dict()
    exportado = json.dumps(spans, default=str)
    assert "/v1/auth/login" in exportado
    assert "vazamento@exemplo.com" not in exportado
    assert SENHA not in exportado
    assert CODIGO not in exportado
