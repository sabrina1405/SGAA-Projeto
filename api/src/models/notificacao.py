import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class TipoNotificacao(enum.StrEnum):
    """Guardado como texto: um tipo novo não exige migração."""

    RECADO = "recado"
    AULA_LEMBRETE_SEMANA = "aula_lembrete_semana"
    AULA_LEMBRETE_DIA = "aula_lembrete_dia"
    AULA_LEMBRETE_30MIN = "aula_lembrete_30min"
    AULA_CANCELADA = "aula_cancelada"
    # A aula e as seguintes da série, num aviso só.
    AULAS_CANCELADAS = "aulas_canceladas"
    # O aluno cancelou a participação; o aviso vai para o professor.
    PARTICIPACAO_CANCELADA = "participacao_cancelada"


class StatusEnvio(enum.StrEnum):
    ENVIADO = "enviado"  # aceito pelo Expo, aguardando o recibo
    OK = "ok"  # entregue ao FCM ou ao APNs
    ERRO = "erro"
    SEM_RECIBO = "sem_recibo"  # o Expo guarda os recibos por 24 horas


class Dispositivo(AuditoriaMixin, Base):
    """Aparelho que recebe push. Logout ou token inválido preenchem `deletado_em`."""

    __tablename__ = "dispositivo"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True)
    plataforma: Mapped[str | None] = mapped_column(String(10))


class Notificacao(AuditoriaMixin, Base):
    """Fila de envio. Os destinatários são resolvidos só na hora do envio."""

    __tablename__ = "notificacao"
    __table_args__ = (
        Index(
            "ix_notificacao_pendente",
            "enviar_em",
            postgresql_where=text("processada_em IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30))
    referencia_id: Mapped[int] = mapped_column(Integer)
    enviar_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tentativas: Mapped[int] = mapped_column(Integer, server_default="0", default=0)


class EnvioPush(AuditoriaMixin, Base):
    """Uma mensagem enviada a um dispositivo, com o ticket para conferir o recibo."""

    __tablename__ = "envio_push"
    __table_args__ = (
        Index(
            "ix_envio_push_aguardando_recibo",
            "criado_em",
            postgresql_where=text("status = 'enviado'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    notificacao_id: Mapped[int] = mapped_column(
        ForeignKey("notificacao.id", ondelete="CASCADE"), index=True
    )
    dispositivo_id: Mapped[int] = mapped_column(
        ForeignKey("dispositivo.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    erro: Mapped[str | None] = mapped_column(String(100))
    verificado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
