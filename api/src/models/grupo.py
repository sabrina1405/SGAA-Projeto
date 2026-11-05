from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class Grupo(AuditoriaMixin, Base):
    __tablename__ = "grupo"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(50))
    descricao: Mapped[str | None] = mapped_column(String(100))
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.usuario_id"), index=True
    )


class GrupoAluno(Base):
    """Vínculo entre grupo e aluno. Sair do grupo apaga a linha."""

    __tablename__ = "grupo_aluno"

    grupo_id: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", ondelete="CASCADE"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
