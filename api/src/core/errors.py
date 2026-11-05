"""Tratadores que põem todo erro no envelope `{sucesso, mensagem, dados}`."""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as HTTPExceptionStarlette

MENSAGEM_VALIDACAO = "Dados inválidos"
MENSAGEM_ERRO_INTERNO = "Erro interno. Tente novamente em instantes."

# Erros gerados pelo próprio framework, que chegam com o texto padrão em inglês.
_MENSAGENS_DO_FRAMEWORK = {
    404: "Recurso não encontrado",
    405: "Método não permitido",
}


class CamposInvalidos(Exception):
    """Erro de validação que só o service consegue apontar.

    Responde `422` no mesmo formato dos erros de validação do corpo.
    """

    def __init__(
        self, tipo: str, mensagem: str, campos: list[str], local: str = "body"
    ) -> None:
        super().__init__(mensagem)
        self.erros = [
            {"local": [local, campo], "tipo": tipo, "mensagem": mensagem}
            for campo in campos
        ]


def _resposta_de_erro(
    status_code: int,
    mensagem: str,
    *,
    erros: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    conteudo: dict[str, Any] = {"sucesso": False, "mensagem": mensagem, "dados": None}
    if erros is not None:
        conteudo["erros"] = erros
    return JSONResponse(status_code=status_code, content=conteudo, headers=headers)


async def tratar_erro_http(_: Request, erro: HTTPExceptionStarlette) -> JSONResponse:
    mensagem = str(erro.detail)
    if mensagem == HTTPStatus(erro.status_code).phrase:
        mensagem = _MENSAGENS_DO_FRAMEWORK.get(erro.status_code, mensagem)
    return _resposta_de_erro(erro.status_code, mensagem, headers=erro.headers)


async def tratar_erro_validacao(
    _: Request, erro: RequestValidationError
) -> JSONResponse:
    # O FastAPI traz o valor recebido em "input" (e às vezes em "ctx"), o que
    # ecoaria senhas e códigos na resposta de erro: só o resto é devolvido.
    erros = [
        {"local": item["loc"], "tipo": item["type"], "mensagem": item["msg"]}
        for item in erro.errors()
    ]
    return _resposta_de_erro(422, MENSAGEM_VALIDACAO, erros=jsonable_encoder(erros))


async def tratar_campos_invalidos(_: Request, erro: CamposInvalidos) -> JSONResponse:
    return _resposta_de_erro(422, MENSAGEM_VALIDACAO, erros=erro.erros)


async def tratar_erro_interno(_: Request, __: Exception) -> JSONResponse:
    # A exceção continua subindo depois da resposta, para o servidor e o
    # Logfire a registrarem; o cliente nunca vê o texto dela.
    return _resposta_de_erro(500, MENSAGEM_ERRO_INTERNO)


def registrar_tratadores(app: FastAPI) -> None:
    app.add_exception_handler(HTTPExceptionStarlette, tratar_erro_http)
    app.add_exception_handler(RequestValidationError, tratar_erro_validacao)
    app.add_exception_handler(CamposInvalidos, tratar_campos_invalidos)
    app.add_exception_handler(Exception, tratar_erro_interno)
