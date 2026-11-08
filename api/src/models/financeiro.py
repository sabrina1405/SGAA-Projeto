import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class FrequenciaPlano(enum.StrEnum):
    MENSAL = "mensal"
    SEMANAL = "semanal"


class StatusCobranca(enum.StrEnum):
    """Vencida não é um status guardado: é a pendente com vencimento passado."""

    PENDENTE = "pendente"
    PAGA = "paga"
    CANCELADA = "cancelada"


class PlanoCobranca(AuditoriaMixin, Base):
    """Cobrança recorrente de um aluno. Encerrar o plano preenche `deletado_em`.

    `dia_vencimento`: 1 a 31 no mensal (no mês mais curto, o último dia) e
    0 (segunda) a 6 (domingo) no semanal.
    """

    __tablename__ = "plano_cobranca"
    __table_args__ = (
        CheckConstraint("valor_centavos > 0", name="ck_plano_cobranca_valor"),
        CheckConstraint(
            "(frequencia = 'mensal' AND dia_vencimento BETWEEN 1 AND 31)"
            " OR (frequencia = 'semanal' AND dia_vencimento BETWEEN 0 AND 6)",
            name="ck_plano_cobranca_dia",
        ),
        CheckConstraint(
            "fim IS NULL OR fim >= inicio", name="ck_plano_cobranca_periodo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.usuario_id"), index=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"), index=True
    )
    descricao: Mapped[str] = mapped_column(String(100))
    valor_centavos: Mapped[int] = mapped_column(Integer)
    frequencia: Mapped[FrequenciaPlano] = mapped_column(
        Enum(
            FrequenciaPlano,
            name="frequencia_plano_enum",
            values_callable=lambda itens: [item.value for item in itens],
        )
    )
    dia_vencimento: Mapped[int] = mapped_column(Integer)
    inicio: Mapped[date] = mapped_column(Date)
    fim: Mapped[date | None] = mapped_column(Date)


class Cobranca(AuditoriaMixin, Base):
    """Valor que o aluno deve à professora, pago por Pix fora do app. A baixa é
    manual. Sem `plano_id`, é avulsa."""

    __tablename__ = "cobranca"
    __table_args__ = (
        CheckConstraint("valor_centavos > 0", name="ck_cobranca_valor"),
        # A geração das recorrentes pode rodar de novo sem duplicar.
        UniqueConstraint("plano_id", "vencimento", name="uq_cobranca_plano_vencimento"),
        Index("ix_cobranca_professor_vencimento", "professor_id", "vencimento"),
        Index("ix_cobranca_aluno_vencimento", "aluno_id", "vencimento"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professor.usuario_id"))
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE")
    )
    plano_id: Mapped[int | None] = mapped_column(ForeignKey("plano_cobranca.id"))
    descricao: Mapped[str] = mapped_column(String(100))
    valor_centavos: Mapped[int] = mapped_column(Integer)
    vencimento: Mapped[date] = mapped_column(Date)
    status: Mapped[StatusCobranca] = mapped_column(
        Enum(
            StatusCobranca,
            name="status_cobranca_enum",
            values_callable=lambda itens: [item.value for item in itens],
        ),
        server_default=StatusCobranca.PENDENTE.value,
        default=StatusCobranca.PENDENTE,
    )
    paga_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
