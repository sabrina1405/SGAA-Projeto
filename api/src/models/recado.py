from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class RecadoGeral(AuditoriaMixin, Base):
    """Painel fixo do professor, visível a todos os alunos.

    Limpar o painel preenche `deletado_em`; salvar de novo reaproveita a linha.
    """

    __tablename__ = "recado_geral"

    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.usuario_id", ondelete="CASCADE"), primary_key=True
    )
    conteudo: Mapped[str] = mapped_column(Text)


class Recado(AuditoriaMixin, Base):
    """Recado com período de exibição. Sem `data_fim`, fica no mural até ser excluído."""

    __tablename__ = "recado"
    __table_args__ = (
        CheckConstraint(
            "data_fim IS NULL OR data_fim >= data_inicio", name="ck_recado_periodo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.usuario_id"), index=True
    )
    conteudo: Mapped[str] = mapped_column(Text)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    # Valem para quem entrar depois do envio também.
    todos_alunos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )
    todos_grupos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )


class RecadoAluno(Base):
    """Aluno destinatário do recado. Trocar os destinatários apaga a linha."""

    __tablename__ = "recado_aluno"

    recado_id: Mapped[int] = mapped_column(
        ForeignKey("recado.id", ondelete="CASCADE"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecadoGrupo(Base):
    """Grupo destinatário do recado. Trocar os destinatários apaga a linha."""

    __tablename__ = "recado_grupo"

    recado_id: Mapped[int] = mapped_column(
        ForeignKey("recado.id", ondelete="CASCADE"), primary_key=True
    )
    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
