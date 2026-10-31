"""Processa a fila de push uma vez, como faz o agendador.

Uso: poetry run python -m src.scripts.processar_notificacoes
"""

from src.services.notificacao_service import executar_tarefa_agendada


def main() -> None:
    resultado = executar_tarefa_agendada()
    print(
        f"Notificações enviadas: {resultado['enviadas']}. "
        f"Recibos conferidos: {resultado['recibos_conferidos']}. "
        f"Arquivos removidos: {resultado['arquivos_removidos']}."
    )


if __name__ == "__main__":
    main()
