from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class Professor(AuditoriaMixin, Base):
    """Dados do professor além dos da conta, criados junto com o usuário."""

    __tablename__ = "professor"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    cnpj: Mapped[str | None] = mapped_column(String(14), unique=True)
    # 77 é o tamanho máximo de uma chave Pix do tipo e-mail.
    chave_pix: Mapped[str | None] = mapped_column(String(77), unique=True)
