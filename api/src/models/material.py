from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class Pasta(AuditoriaMixin, Base):
    """Pasta de materiais do professor. Os destinatários ficam na raiz e valem
    para toda a árvore abaixo dela."""

    __tablename__ = "pasta"
    __table_args__ = (
        # Duas pastas com o mesmo nome no mesmo lugar confundem o aluno.
        Index(
            "uq_pasta_nome_no_lugar",
            "professor_id",
            func.coalesce(text("pasta_pai_id"), 0),
            func.lower(text("nome")),
            unique=True,
            postgresql_where=text("deletado_em IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.usuario_id"), index=True
    )
    # Nulo na raiz.
    pasta_pai_id: Mapped[int | None] = mapped_column(ForeignKey("pasta.id"), index=True)
    # A própria pasta, na raiz. Evita subir a árvore para conferir quem vê.
    raiz_id: Mapped[int | None] = mapped_column(ForeignKey("pasta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    # Só valem na raiz, também para quem entrar depois.
    todos_alunos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )
    todos_grupos: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False
    )


class PastaAluno(Base):
    """Aluno que vê a pasta raiz. Trocar os destinatários apaga a linha."""

    __tablename__ = "pasta_aluno"

    pasta_id: Mapped[int] = mapped_column(
        ForeignKey("pasta.id", ondelete="CASCADE"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PastaGrupo(Base):
    """Grupo que vê a pasta raiz. Trocar os destinatários apaga a linha."""

    __tablename__ = "pasta_grupo"

    pasta_id: Mapped[int] = mapped_column(
        ForeignKey("pasta.id", ondelete="CASCADE"), primary_key=True
    )
    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnexoPasta(Base):
    """Material (apostila) guardado na pasta."""

    __tablename__ = "anexo_pasta"

    pasta_id: Mapped[int] = mapped_column(
        ForeignKey("pasta.id", ondelete="CASCADE"), index=True
    )
    arquivo_id: Mapped[int] = mapped_column(
        ForeignKey("arquivo.id", ondelete="CASCADE"), primary_key=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
