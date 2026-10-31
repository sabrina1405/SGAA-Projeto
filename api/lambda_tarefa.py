"""Ponto de entrada da tarefa agendada na AWS Lambda: o EventBridge chama a
cada 5 minutos para enviar a fila de push e conferir os recibos do Expo."""

import json
import os
from typing import Any

from src.core.parametros import carregar_parametros

# Antes de importar a aplicação, que lê a configuração ao ser importada.
carregar_parametros()

import logfire

from src.core.observabilidade import FLUSH_TIMEOUT_MS, configurar_logfire
from src.main import app
from src.services.notificacao_service import executar_tarefa_agendada

LOGFIRE_LIGADO = configurar_logfire(os.getenv("AMBIENTE", "dev"), app.version)


def handler(_evento: Any, _contexto: Any) -> dict[str, int]:
    try:
        resultado = executar_tarefa_agendada()
        # Vai para o CloudWatch Logs da função.
        print(json.dumps(resultado))
        return resultado
    finally:
        if LOGFIRE_LIGADO:
            logfire.force_flush(FLUSH_TIMEOUT_MS)
