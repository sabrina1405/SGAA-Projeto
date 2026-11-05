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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class StatusEntrega(enum.StrEnum):
    ENVIADO = "enviado"
    ENTREGUE_COM_ATRASO = "entregue_com_atraso"


class Atividade(AuditoriaMixin, Base):
    """Atividade do professor. Os destinatários são dinâmicos, como nos recados:
    quem entra depois em um grupo passa a vê-la."""

    __tablename__ = "atividade"
    __table_args__ = (
        CheckConstraint("vence_em > liberar_em", name="ck_atividade_periodo"),
        Index("ix_atividade_professor_id_vence_em", "professor_id", "vence_em"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professor.usuario_id"))
    titulo: Mapped[str] = mapped_column(String(75))
    # Em Markdown, renderizado pelo front.
    descricao: Mapped[str] = mapped_column(Text)
    permite_envio_arquivo: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )
    liberar_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vence_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    todos_alunos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )
    todos_grupos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )


class AtividadeAluno(Base):
    """Aluno destinatário. Trocar os destinatários apaga a linha."""

    __tablename__ = "atividade_aluno"

    atividade_id: Mapped[int] = mapped_column(
        ForeignKey("atividade.id", ondelete="CASCADE"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AtividadeGrupo(Base):
    """Grupo destinatário. Trocar os destinatários apaga a linha."""

    __tablename__ = "atividade_grupo"

    atividade_id: Mapped[int] = mapped_column(
        ForeignKey("atividade.id", ondelete="CASCADE"), primary_key=True
    )
    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnexoAtividade(Base):
    __tablename__ = "anexo_atividade"

    atividade_id: Mapped[int] = mapped_column(
        ForeignKey("atividade.id", ondelete="CASCADE"), primary_key=True
    )
    arquivo_id: Mapped[int] = mapped_column(
        ForeignKey("arquivo.id", ondelete="CASCADE"), primary_key=True, unique=True
    )


class EntregaAtividade(AuditoriaMixin, Base):
    """Resposta do aluno. Uma por atividade; editá-la reaproveita a linha."""

    __tablename__ = "entrega_atividade"
    __table_args__ = (
        UniqueConstraint(
            "atividade_id", "aluno_id", name="uq_entrega_atividade_atividade_aluno"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    atividade_id: Mapped[int] = mapped_column(
        ForeignKey("atividade.id", ondelete="CASCADE")
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"), index=True
    )
    resposta: Mapped[str] = mapped_column(Text)
    status: Mapped[StatusEntrega] = mapped_column(
        Enum(
            StatusEntrega,
            name="status_entrega_enum",
            values_callable=lambda itens: [item.value for item in itens],
        ),
        server_default=StatusEntrega.ENVIADO.value,
        default=StatusEntrega.ENVIADO,
    )
    enviada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AnexoEntrega(Base):
    __tablename__ = "anexo_entrega"

    entrega_id: Mapped[int] = mapped_column(
        ForeignKey("entrega_atividade.id", ondelete="CASCADE"), primary_key=True
    )
    arquivo_id: Mapped[int] = mapped_column(
        ForeignKey("arquivo.id", ondelete="CASCADE"), primary_key=True, unique=True
    )
