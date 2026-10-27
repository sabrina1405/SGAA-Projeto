"""Fila de notificações push.

Cada feature enfileira com `agendar` na própria transação e fornece um
resolvedor, que monta a mensagem e os destinatários na hora do envio. O
envio acontece logo depois da requisição (quando a notificação já venceu)
e, de novo, na tarefa agendada, que também cobre as falhas e os agendamentos.
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.core.database import obter_engine
from src.core.push import (
    DISPOSITIVO_NAO_REGISTRADO,
    MENSAGENS_POR_ENVIO,
    EnviadorPush,
    FalhaPush,
    MensagemPush,
    Ticket,
    obter_enviador_push,
)
from src.core.security import agora
from src.models.notificacao import (
    Dispositivo,
    EnvioPush,
    Notificacao,
    StatusEnvio,
    TipoNotificacao,
)

logger = logging.getLogger(__name__)

MAXIMO_TENTATIVAS = 5
INTERVALO_ENTRE_TENTATIVAS = timedelta(minutes=5)
# O recibo fica pronto em poucos minutos e some depois de 24 horas.
ESPERA_PELO_RECIBO = timedelta(minutes=15)
VALIDADE_DO_RECIBO = timedelta(hours=24)


@dataclass(frozen=True)
class Conteudo:
    usuario_ids: Sequence[int]
    titulo: str
    corpo: str
    # Vai para o app junto com a notificação, para abrir a tela certa.
    dados: dict[str, Any] = field(default_factory=dict)


Resolvedor = Callable[[Session, int], Conteudo | None]


def _resolvedores() -> dict[TipoNotificacao, Resolvedor]:
    # Import local: os services das features importam este módulo para agendar.
    from src.services import aula_service, recado_service

    return {
        TipoNotificacao.RECADO: recado_service.conteudo_da_notificacao,
        **aula_service.RESOLVEDORES,
    }


def agendar(
    sessao: Session, tipo: TipoNotificacao, referencia_id: int, enviar_em: datetime
) -> None:
    """Não faz commit: entra na transação da feature."""
    sessao.add(Notificacao(tipo=tipo, referencia_id=referencia_id, enviar_em=enviar_em))


def reagendar(
    sessao: Session, tipo: TipoNotificacao, referencia_id: int, enviar_em: datetime
) -> None:
    """Muda o horário das notificações ainda não enviadas. Não faz commit."""
    sessao.execute(
        update(Notificacao)
        .where(
            Notificacao.tipo == tipo,
            Notificacao.referencia_id == referencia_id,
            Notificacao.processada_em.is_(None),
        )
        .values(enviar_em=enviar_em)
    )


def cancelar_pendentes(
    sessao: Session, tipo: TipoNotificacao, referencia_id: int
) -> None:
    """Descarta as notificações ainda não enviadas. Não faz commit."""
    sessao.execute(
        update(Notificacao)
        .where(
            Notificacao.tipo == tipo,
            Notificacao.referencia_id == referencia_id,
            Notificacao.processada_em.is_(None),
            Notificacao.deletado_em.is_(None),
        )
        .values(deletado_em=agora())
    )


def _proxima_pendente(sessao: Session) -> Notificacao | None:
    # SKIP LOCKED: a tarefa agendada e o envio logo após a requisição podem
    # rodar ao mesmo tempo sem mandar a mesma notificação duas vezes.
    return sessao.scalar(
        select(Notificacao)
        .where(
            Notificacao.processada_em.is_(None),
            Notificacao.deletado_em.is_(None),
            Notificacao.enviar_em <= agora(),
            Notificacao.tentativas < MAXIMO_TENTATIVAS,
        )
        .order_by(Notificacao.enviar_em, Notificacao.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )


def _registro_do_envio(
    notificacao: Notificacao, dispositivo: Dispositivo, ticket: Ticket
) -> EnvioPush:
    if not ticket.ok:
        status = StatusEnvio.ERRO
    elif ticket.id is None:
        status = StatusEnvio.OK  # backend console: não há recibo para conferir
    else:
        status = StatusEnvio.ENVIADO
    return EnvioPush(
        notificacao_id=notificacao.id,
        dispositivo_id=dispositivo.id,
        ticket_id=ticket.id,
        status=status,
        erro=ticket.erro,
    )


def _enviar(sessao: Session, enviador: EnviadorPush, notificacao: Notificacao) -> None:
    conteudo = _resolvedores()[TipoNotificacao(notificacao.tipo)](
        sessao, notificacao.referencia_id
    )
    if conteudo is not None and conteudo.usuario_ids:
        ja_enviados = select(EnvioPush.dispositivo_id).where(
            EnvioPush.notificacao_id == notificacao.id
        )
        # Numa nova tentativa, quem já recebeu não recebe de novo.
        dispositivos = sessao.scalars(
            select(Dispositivo)
            .where(
                Dispositivo.usuario_id.in_(conteudo.usuario_ids),
                Dispositivo.deletado_em.is_(None),
                Dispositivo.id.not_in(ja_enviados),
            )
            .order_by(Dispositivo.id)
        ).all()
        # Lote a lote: se um lote falhar, os anteriores ficam registrados e a
        # nova tentativa não os repete.
        for inicio in range(0, len(dispositivos), MENSAGENS_POR_ENVIO):
            lote = dispositivos[inicio : inicio + MENSAGENS_POR_ENVIO]
            tickets = enviador.enviar(
                [
                    MensagemPush(
                        token=dispositivo.token,
                        titulo=conteudo.titulo,
                        corpo=conteudo.corpo,
                        dados=conteudo.dados,
                    )
                    for dispositivo in lote
                ]
            )
            for dispositivo, ticket in zip(lote, tickets, strict=True):
                sessao.add(_registro_do_envio(notificacao, dispositivo, ticket))
                if ticket.erro == DISPOSITIVO_NAO_REGISTRADO:
                    dispositivo.deletado_em = agora()
            sessao.flush()
    notificacao.processada_em = agora()


def _proxima_tentativa(tentativas: int) -> datetime:
    """Espera mais a cada falha, para não gastar as tentativas na mesma execução."""
    return agora() + INTERVALO_ENTRE_TENTATIVAS * tentativas


def processar_pendentes(
    sessao: Session, enviador: EnviadorPush, *, limite: int = 50
) -> int:
    """Envia as notificações vencidas, uma por transação. Devolve quantas saíram
    da fila; as que falharam voltam para uma nova tentativa."""
    processadas = 0
    for _ in range(limite):
        notificacao = _proxima_pendente(sessao)
        if notificacao is None:
            break
        try:
            _enviar(sessao, enviador, notificacao)
        except FalhaPush:
            # Os lotes que já saíram ficam registrados.
            logger.exception("Falha ao enviar a notificação %s", notificacao.id)
            notificacao.tentativas += 1
            notificacao.enviar_em = _proxima_tentativa(notificacao.tentativas)
            sessao.commit()
            continue
        except Exception:
            # Um erro inesperado não pode travar a fila: conta como tentativa.
            logger.exception("Erro ao processar a notificação %s", notificacao.id)
            notificacao_id, tentativas = notificacao.id, notificacao.tentativas + 1
            sessao.rollback()
            sessao.execute(
                update(Notificacao)
                .where(Notificacao.id == notificacao_id)
                .values(tentativas=tentativas, enviar_em=_proxima_tentativa(tentativas))
            )
            sessao.commit()
            continue
        sessao.commit()
        processadas += 1
    return processadas


def processar_pendentes_sem_falhar(sessao: Session, enviador: EnviadorPush) -> None:
    """Envio logo após a requisição. Um erro aqui fica para a tarefa agendada."""
    try:
        processar_pendentes(sessao, enviador, limite=10)
    except Exception:
        logger.exception("Falha no envio imediato das notificações")
        sessao.rollback()


def conferir_recibos(sessao: Session, enviador: EnviadorPush) -> int:
    """Atualiza os envios com o recibo do Expo e desativa os tokens que não
    valem mais. Devolve quantos envios foram conferidos."""
    momento = agora()
    envios = sessao.scalars(
        select(EnvioPush)
        .where(
            EnvioPush.status == StatusEnvio.ENVIADO,
            EnvioPush.criado_em <= momento - ESPERA_PELO_RECIBO,
        )
        .order_by(EnvioPush.id)
        .limit(1000)
    ).all()
    if not envios:
        return 0
    try:
        recibos = enviador.consultar_recibos([envio.ticket_id for envio in envios])
    except FalhaPush:
        logger.exception("Falha ao consultar os recibos do Expo")
        return 0

    conferidos = 0
    for envio in envios:
        recibo = recibos.get(envio.ticket_id)
        if recibo is None:
            if envio.criado_em > momento - VALIDADE_DO_RECIBO:
                continue
            envio.status = StatusEnvio.SEM_RECIBO
        elif recibo.ok:
            envio.status = StatusEnvio.OK
        else:
            envio.status = StatusEnvio.ERRO
            envio.erro = recibo.erro
            if recibo.erro == DISPOSITIVO_NAO_REGISTRADO:
                sessao.execute(
                    update(Dispositivo)
                    .where(
                        Dispositivo.id == envio.dispositivo_id,
                        Dispositivo.deletado_em.is_(None),
                    )
                    .values(deletado_em=momento)
                )
        envio.verificado_em = momento
        conferidos += 1
    sessao.commit()
    return conferidos


def executar_tarefa_agendada() -> dict[str, int]:
    """Ponto de entrada do agendador (EventBridge) e do script local."""
    enviador = obter_enviador_push()
    with Session(obter_engine(), expire_on_commit=False) as sessao:
        return {
            "enviadas": processar_pendentes(sessao, enviador),
            "recibos_conferidos": conferir_recibos(sessao, enviador),
        }
