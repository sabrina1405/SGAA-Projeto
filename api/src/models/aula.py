import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class StatusAula(enum.StrEnum):
    AGENDADA = "agendada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class StatusParticipacao(enum.StrEnum):
    ATIVA = "ativa"
    CANCELADA = "cancelada"  # pelo aluno


def _valores(enumeracao: type[enum.StrEnum]) -> list[str]:
    return [item.value for item in enumeracao]


class Aula(AuditoriaMixin, Base):
    """Aula do professor. As ocorrências de uma série semanal apontam, em
    `serie_id`, para a primeira delas (que aponta para si mesma)."""

    __tablename__ = "aula"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="ck_aula_horario"),
        Index("ix_aula_professor_id_inicio", "professor_id", "inicio"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professor.usuario_id"))
    serie_id: Mapped[int | None] = mapped_column(ForeignKey("aula.id"), index=True)
    reposicao_de_aula_id: Mapped[int | None] = mapped_column(ForeignKey("aula.id"))
    titulo: Mapped[str] = mapped_column(String(75))
    descricao: Mapped[str | None] = mapped_column(String(150))
    # Notas do professor; o aluno não vê.
    anotacoes: Mapped[str | None] = mapped_column(Text)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[StatusAula] = mapped_column(
        Enum(StatusAula, name="status_aula_enum", values_callable=_valores),
        server_default=StatusAula.AGENDADA.value,
        default=StatusAula.AGENDADA,
    )
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(150))


class AulaAluno(Base):
    """Participação do aluno na aula.

    O aluno que cancela fica com `repor` marcado até o professor criar a aula
    de reposição (`reposta_em_aula_id`) ou dispensar a pendência.
    """

    __tablename__ = "aula_aluno"

    # Identifica a participação na fila de notificações.
    id: Mapped[int] = mapped_column(Integer, Identity(), unique=True)
    aula_id: Mapped[int] = mapped_column(
        ForeignKey("aula.id", ondelete="CASCADE"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    status: Mapped[StatusParticipacao] = mapped_column(
        Enum(
            StatusParticipacao,
            name="status_participacao_enum",
            values_callable=_valores,
        ),
        server_default=StatusParticipacao.ATIVA.value,
        default=StatusParticipacao.ATIVA,
    )
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(150))
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    repor: Mapped[bool] = mapped_column(Boolean, server_default="false", default=False)
    reposta_em_aula_id: Mapped[int | None] = mapped_column(ForeignKey("aula.id"))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AulaGrupo(Base):
    """Grupo usado ao montar a aula. Os alunos dele viram linhas de `aula_aluno`."""

    __tablename__ = "aula_grupo"

    aula_id: Mapped[int] = mapped_column(
        ForeignKey("aula.id", ondelete="CASCADE"), primary_key=True
    )
    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
