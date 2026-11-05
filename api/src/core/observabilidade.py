import logging
import os
from typing import Any

import logfire
from anyio import to_thread
from fastapi import FastAPI
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.config import obter_config

logger = logging.getLogger(__name__)

# A limpeza padrão do Logfire só conhece nomes em inglês (password, secret...).
PADROES_SENSIVEIS = ["senha", "cpf", "codigo", "telefone", "token"]

FLUSH_TIMEOUT_MS = 2000


def _sem_valores(_: Any, atributos: dict[str, Any]) -> dict[str, Any]:
    # Os argumentos das rotas carregam CPF, telefone, e-mail e códigos, e cada
    # erro de validação traz o valor recebido em "input": nada disso é enviado.
    # A mensagem também fica de fora, porque um validador pode citar nela o
    # valor rejeitado (o de e-mail faz isso) e o Logfire não a limpa.
    return {
        "errors": [
            {"type": erro.get("type"), "loc": erro.get("loc")}
            for erro in atributos.get("errors", [])
        ]
    }


class FlushMiddleware:
    """Envia os registros pendentes ao fim de cada requisição.

    Em serverless a instância pode ser congelada logo após a resposta, antes de
    o envio em lote acontecer.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        finally:
            if scope["type"] == "http":
                try:
                    await to_thread.run_sync(logfire.force_flush, FLUSH_TIMEOUT_MS)
                except Exception:
                    # A telemetria nunca pode derrubar a requisição.
                    logger.exception("Falha ao enviar registros ao Logfire")


def configurar_logfire(ambiente: str, versao: str) -> bool:
    """Liga o envio de registros e das consultas ao banco. Sem LOGFIRE_TOKEN,
    não faz nada."""
    token = obter_config().logfire_token
    if token is None:
        return False

    logfire.configure(
        token=token.get_secret_value(),
        service_name="sgaa-api",
        service_version=versao,
        environment=ambiente,
        console=False,
        scrubbing=logfire.ScrubbingOptions(extra_patterns=PADROES_SENSIVEIS),
    )
    # No driver, e não no SQLAlchemy: a instrumentação do SQLAlchemy ainda não
    # aceita a versão 2.1. Os parâmetros das consultas não são capturados.
    logfire.instrument_psycopg()

    logging.getLogger().addHandler(logfire.LogfireLoggingHandler())
    return True


def configurar_observabilidade(
    app_rotas: FastAPI, app_externo: FastAPI, ambiente: str
) -> bool:
    """Liga o Logfire e instrumenta as rotas. Sem LOGFIRE_TOKEN, não faz nada."""
    if not configurar_logfire(ambiente, app_rotas.version):
        return False
    logfire.instrument_fastapi(app_rotas, request_attributes_mapper=_sem_valores)
    if em_serverless():
        app_externo.add_middleware(FlushMiddleware)
    return True


def em_serverless() -> bool:
    """Na Vercel ou na AWS Lambda, onde a instância congela após a resposta."""
    return bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
